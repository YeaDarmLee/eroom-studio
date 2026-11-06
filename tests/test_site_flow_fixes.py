"""Every test uses create_app('testing'): SQLite only, scheduler/SMS disabled."""
import json
import os
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch

from app import create_app
from app.extensions import db
from app.models import Branch, Room, User, Contract
from app.models.request import Request
from app.models.coupon import Coupon
from app.models.branch import RoomImage, BranchImage
from app.models.sms import SmsTemplate, SmsLog
from app.services.auth_service import AuthService
from app.utils.sms_service import sms_service


class SiteFlowFixesTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.context = self.app.app_context()
        self.context.push()
        self.assertEqual(db.engine.url.get_backend_name(), 'sqlite')
        db.create_all()
        self.files = tempfile.TemporaryDirectory(prefix='site-flow-', dir=Path(__file__).parent)
        self.app.config['UPLOAD_FOLDER'] = self.files.name
        self.client = self.app.test_client()
        self.user = User(name='테스트', email='tenant@example.test', phone='01011112222')
        self.admin = User(name='관리자', email='admin@example.test', role='admin')
        self.branch = Branch(name='테스트점')
        db.session.add_all([self.user, self.admin, self.branch]); db.session.flush()
        self.room = Room(branch_id=self.branch.id, name='101', price=500000, deposit=300000, status='available')
        self.hourly = Room(branch_id=self.branch.id, name='시간제', room_type='time_based', price=10000, deposit=0, status='available')
        db.session.add_all([self.room, self.hourly]); db.session.commit()
        self.u = {'Authorization': 'Bearer ' + AuthService.generate_token(self.user.id)}
        self.a = {'Authorization': 'Bearer ' + AuthService.generate_token(self.admin.id)}
        self.no_provider = patch.object(sms_service, '_get_provider', side_effect=AssertionError('External SMS forbidden'))
        self.provider = self.no_provider.start()

    def tearDown(self):
        self.no_provider.stop()
        db.session.remove(); db.drop_all(); self.context.pop(); self.files.cleanup()

    def contract(self, **kwargs):
        data = dict(user_id=self.user.id, room_id=self.room.id, start_date=date(2026,12,1),
                    end_date=date(2027,1,31), months=2, price=500000, deposit=300000, status='active', payment_day=1)
        data.update(kwargs)
        c = Contract(**data); db.session.add(c); db.session.commit(); return c

    def apply(self, **kwargs):
        data = dict(room_id=self.room.id, start_date='2026-12-01', months=2)
        data.update(kwargs)
        return self.client.post('/api/contracts', headers=self.u, json=data)

    def coupon(self, **kwargs):
        data = dict(code='FLOW', discount_type='fixed', discount_value=10000, discount_cycle='monthly',
                    valid_from=date(2026,1,1), valid_until=date(2030,1,1), used_count=0)
        data.update(kwargs)
        c=Coupon(**data);db.session.add(c);db.session.commit();return c

    def test_local_and_test_ignore_production_url_and_block_delivery(self):
        with patch.dict(os.environ, {'DATABASE_URL':'mysql://production-must-never-be-used/db'}):
            isolated = create_app('testing')
            with isolated.app_context():
                self.assertEqual(db.engine.url.get_backend_name(), 'sqlite')
                self.assertFalse(isolated.config['SMS_ENABLED'])
                self.assertFalse(isolated.config['SCHEDULER_ENABLED'])
        with self.assertRaises(RuntimeError):
            create_app('testing', {'SQLALCHEMY_DATABASE_URI':'mysql://forbidden/db'})
        self.assertTrue(sms_service.send_sms(1, 'TEST', {})[0])
        self.provider.assert_not_called()

    def test_mock_login_is_unavailable(self):
        for path in ('mock-login','mock-admin-login'):
            self.assertEqual(self.client.post('/api/auth/'+path).status_code,404)

    def test_contract_claim_requires_admin_verification(self):
        c=self.contract(user_id=None,temp_user_phone='01099998888')
        r=self.client.post('/api/auth/email-register',json=dict(name='신규',email='new@example.test',phone='01099998888',password='test-password'))
        self.assertEqual(r.status_code,201)
        self.assertIsNone(c.user_id)
        req=Request.query.filter_by(type='account_link').first()
        path=f'/admin/api/requests/{req.id}/status'
        self.assertEqual(self.client.put(path,headers=self.a,json={'status':'done'}).status_code,400)
        self.assertEqual(self.client.put(path,headers=self.a,json={'status':'done','identity_verified':True}).status_code,200)
        self.assertEqual(c.user_id,r.json['user']['id'])

    def test_placeholder_registration_and_verified_transfer(self):
        legacy=User(email='temp_old@example.test',phone='01099998888');db.session.add(legacy);db.session.commit()
        c=self.contract(user_id=legacy.id)
        r=self.client.post('/api/auth/email-register',json=dict(name='실제',email='real@example.test',phone=legacy.phone,password='test-password'))
        self.assertEqual(r.status_code,201)
        self.assertEqual(c.user_id,legacy.id)
        req=Request.query.filter_by(type='account_link').first()
        approved=self.client.put(f'/admin/api/requests/{req.id}/status',headers=self.a,json={'status':'done','identity_verified':True})
        self.assertEqual(approved.status_code,200)
        self.assertEqual(c.user_id,r.json['user']['id'])
        self.assertIsNone(legacy.phone)
        self.assertEqual(db.session.get(User,c.user_id).phone,'01099998888')

    def test_coupon_count_lists_and_validation(self):
        coupon=self.coupon()
        r=self.apply(coupon_code=coupon.code)
        self.assertEqual(r.status_code,201)
        self.assertEqual(coupon.used_count,1)
        for path,headers in [('/api/contracts',self.u),('/admin/api/contracts',self.a),(f'/admin/api/contracts/{r.json["id"]}',self.a)]:
            self.assertEqual(self.client.get(path,headers=headers).status_code,200)

    def test_invalid_coupon_is_not_consumed(self):
        c=self.coupon(min_months=12)
        self.assertEqual(self.apply(coupon_code=c.code).status_code,400)
        self.assertEqual(c.used_count,0)
        self.assertEqual(Contract.query.count(),0)

    def test_large_discount_never_creates_negative_rent(self):
        c=self.coupon(discount_value=900000)
        r=self.apply(coupon_code=c.code)
        self.assertEqual(r.status_code,201)
        self.assertGreaterEqual(r.json['price'],0)
        self.assertGreaterEqual(r.json['initial_payment'],0)

    def test_invalid_periods_return_client_error(self):
        for months in (-1,0,True,'bad',1.5):
            self.assertEqual(self.apply(months=months).status_code,400)
        self.assertEqual(Contract.query.count(),0)

    def test_pending_termination_blocks_overlap_and_reserves_room(self):
        self.contract(status='terminate_requested',termination_effective_date=date(2027,1,10))
        self.assertEqual(self.apply().status_code,409)
        self.assertEqual(Contract.query.count(),1)

    def test_new_application_updates_public_room_status(self):
        self.assertEqual(self.apply().status_code,201)
        self.assertEqual(self.client.get(f'/api/public/rooms/{self.room.id}').json['status'],'reserved')

    def test_hourly_price_derived_from_times_and_all_snapshots_agree(self):
        r=self.apply(room_id=self.hourly.id,start_time='09:00',end_time='12:00',hours=0)
        self.assertEqual(r.status_code,201)
        self.assertEqual(r.json['price'],30000)
        self.assertEqual(r.json['initial_payment'],30000)
        c=db.session.get(Contract,r.json['id'])
        self.assertEqual(json.loads(c.discount_details)['first_month_rent'],30000)
        self.assertEqual(self.hourly.status,'available')
        self.assertEqual(self.apply(room_id=self.hourly.id,start_time='12:00',end_time='13:00').status_code,201)
        self.assertEqual(self.apply(room_id=self.hourly.id,start_time='12:00',end_time='09:00').status_code,400)

    def test_signature_waiting_is_visible_in_timeline_and_blocks_booking(self):
        self.contract(room_id=self.hourly.id,start_date=date(2026,12,1),end_date=date(2026,12,1),start_time='09:00',end_time='12:00',status='waiting_signature')
        self.assertEqual(len(self.client.get(f'/api/public/rooms/{self.hourly.id}/reservations?date=2026-12-01').json),1)
        self.assertEqual(self.apply(room_id=self.hourly.id,start_time='10:00',end_time='11:00').status_code,409)

    def test_extension_approval_is_idempotent(self):
        c=self.contract()
        req=Request(user_id=self.user.id,contract_id=c.id,type='extension',status='submitted',details=json.dumps({'extension_months':1}))
        db.session.add(req);db.session.commit()
        path=f'/admin/api/requests/{req.id}/status'
        self.assertEqual(self.client.put(path,headers=self.a,json={'status':'done'}).status_code,200)
        end=c.end_date
        self.assertEqual(self.client.put(path,headers=self.a,json={'status':'done','admin_response':'답변 수정'}).status_code,200)
        self.assertEqual(c.end_date,end)

    def test_extension_cannot_overlap_following_contract(self):
        c=self.contract()
        self.contract(start_date=date(2027,2,1),end_date=date(2027,3,31),status='approved')
        req=Request(user_id=self.user.id,contract_id=c.id,type='extension',status='submitted',details=json.dumps({'extension_months':1}))
        db.session.add(req);db.session.commit()
        self.assertEqual(self.client.put(f'/admin/api/requests/{req.id}/status',headers=self.a,json={'status':'done'}).status_code,409)
        self.assertEqual(c.end_date,date(2027,1,31))

    def test_unmapped_create_and_inquiry_context(self):
        r=self.client.post('/admin/api/contracts/unmapped',headers=self.a,json={'room_id':self.room.id,'temp_user_phone':'01099998888','start_date':'2026-12-01','end_date':'2027-01-31'})
        self.assertEqual(r.status_code,201)
        self.assertEqual(self.room.status,'occupied')
        self.client.post('/api/requests',headers=self.u,json={'type':'inquiry','details':{'room_id':self.room.id,'message':'문의'}})
        row=self.client.get('/admin/api/requests',headers=self.a).json[0]
        self.assertEqual(row['room_name'],'101')
        self.assertEqual(row['branch_id'],self.branch.id)

    def test_rent_includes_pending_termination_and_monthly_discount(self):
        c=self.contract(status='terminate_requested',termination_effective_date=date(2026,12,31))
        self.client.post(f'/admin/api/contracts/{c.id}/custom-discounts',headers=self.a,json={'target_month':'2026-12','amount':100000,'reason':'테스트'})
        rows=self.client.get('/admin/api/rent-management-contracts?month=2026-12',headers=self.a).json
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['price'],400000)
        self.assertEqual(self.client.get('/admin/api/rent-management-contracts?month=2027-03',headers=self.a).json,[])

    def test_history_deletes_return_clear_client_errors(self):
        c=self.contract(status='terminated')
        self.assertEqual(self.client.delete(f'/admin/api/rooms/{self.room.id}',headers=self.a).status_code,400)
        self.assertEqual(self.client.delete(f'/admin/api/users/{self.user.id}',headers=self.a).status_code,409)
        self.assertEqual(self.client.delete(f'/admin/api/branches/{self.branch.id}?force=true',headers=self.a).status_code,409)
        self.assertIsNotNone(db.session.get(Contract,c.id))

    def test_image_names_unique_and_main_reference_repaired(self):
        for _ in range(2):
            self.assertEqual(self.client.post(f'/admin/api/rooms/{self.room.id}/images',headers=self.a,data={'images':(BytesIO(b'fixture'),'same.png')}).status_code,201)
        images=RoomImage.query.all();self.assertNotEqual(images[0].image_url,images[1].image_url)
        self.client.delete(f'/admin/api/rooms/{self.room.id}/images/{images[0].id}',headers=self.a)
        self.assertTrue((Path(self.files.name)/Path(images[1].image_url).name).exists() or (Path(self.files.name)/'rooms'/Path(images[1].image_url).name).exists())
        self.client.post(f'/admin/api/branches/{self.branch.id}/images',headers=self.a,data={'images':(BytesIO(b'fixture'),'main.png')})
        image=BranchImage.query.first()
        self.client.delete(f'/admin/api/branches/{self.branch.id}/images/{image.id}',headers=self.a)
        self.assertIsNone(self.branch.image_url)

    def test_active_contract_cannot_reject_signature(self):
        c=self.contract()
        self.assertEqual(self.client.post(f'/api/contracts/{c.id}/reject',headers=self.u,json={'reason':'테스트'}).status_code,409)
        self.assertEqual(c.status,'active')

    def test_legacy_entries_redirect_and_orphan_extension_rejected(self):
        for path in ('/onboarding/link','/requests/new','/admin/rent-management'):
            r=self.client.get(path,headers=self.a);self.assertEqual(r.status_code,302)
        r=self.client.post('/api/requests',headers=self.u,json={'type':'extension','details':{'months':1}})
        self.assertEqual(r.status_code,400)

    def test_failed_sms_can_retry_without_duplicate_log(self):
        c=self.contract()
        db.session.add(SmsTemplate(type='TEST',title='테스트',content='안내',is_active=True));db.session.commit()
        provider=Mock();provider.send.side_effect=[RuntimeError('isolated failure'),'success-id']
        with patch.dict(self.app.config,{'SMS_ENABLED':True}),patch.object(sms_service,'_get_provider',return_value=(provider,'TEST')):
            results=[sms_service.send_sms(c.id,'TEST',{'user_phone':self.user.phone}) for _ in range(3)]
        self.assertFalse(results[0][0]);self.assertTrue(results[1][0]);self.assertTrue(results[2][0])
        self.assertEqual(provider.send.call_count,2);self.assertEqual(SmsLog.query.count(),1)

    def test_manual_rent_sms_uses_selected_month(self):
        c=self.contract()
        with patch.object(sms_service,'send_sms',return_value=(True,'isolated mock')) as send:
            r=self.client.post('/admin/api/sms/manual',headers=self.a,json={'contract_id':c.id,'type':'PAYMENT_OVERDUE_STAGE1','target_month':'2026-12'})
            self.assertEqual(r.status_code,200)
            self.assertEqual(send.call_args.kwargs['context']['month_key'],'2026-12')
            self.assertEqual(send.call_args.kwargs['context']['due_date'],'2026-12-01')
            self.assertEqual(self.client.post('/admin/api/sms/manual',headers=self.a,json={'contract_id':c.id,'type':'PAYMENT_OVERDUE_STAGE1','target_month':'2027-03'}).status_code,400)
            self.assertEqual(send.call_count,1)

    def test_expiry_preserves_following_reservation(self):
        from app.tasks import terminate_expired_contracts
        today=datetime.now(timezone(timedelta(hours=9))).date()
        self.contract(start_date=today-timedelta(days=60),end_date=today-timedelta(days=1))
        self.contract(start_date=today+timedelta(days=10),end_date=today+timedelta(days=70),status='waiting_signature')
        self.room.status='occupied';db.session.commit()
        terminate_expired_contracts(self.app)
        self.assertEqual(self.room.status,'reserved')


class MigrationIsolationTest(unittest.TestCase):
    def test_legacy_upgrade_keeps_data_and_adds_current_schema(self):
        from flask_migrate import upgrade
        from sqlalchemy import inspect, text
        app=create_app('testing')
        with app.app_context():
            self.assertEqual(db.engine.url.get_backend_name(),'sqlite')
            directory=str(Path(__file__).resolve().parents[1]/'migrations')
            upgrade(directory=directory,revision='7626f8865d63')
            db.session.execute(text("INSERT INTO users (id,name) VALUES (1,'legacy')"))
            db.session.execute(text("INSERT INTO branches (id,name) VALUES (1,'legacy')"))
            db.session.execute(text("INSERT INTO rooms (id,branch_id,name) VALUES (1,1,'101')"))
            db.session.execute(text("INSERT INTO contracts (id,user_id,room_id,start_date,end_date,total_price) VALUES (1,1,1,'2026-12-01','2027-01-31',500000)"))
            db.session.commit()
            upgrade(directory=directory)
            self.assertEqual(db.session.execute(text('SELECT price,total_price FROM contracts WHERE id=1')).one(),(500000,500000))
            self.assertTrue(set(db.metadata.tables).issubset(inspect(db.engine).get_table_names()))
            self.assertTrue(inspect(db.engine).get_columns('contracts')[1]['nullable'])
            db.session.remove(); db.drop_all()
