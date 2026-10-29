"""Run against an isolated in-memory DB; never starts the production scheduler."""
import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from flask import Flask
from app.extensions import db
from app.models import User, Branch, Room, Contract
from app.models.request import Request
from app.routes.admin import admin_bp
from app.tasks import terminate_expired_contracts


class AdminTerminationApprovalTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, SECRET_KEY='test',
                               SQLALCHEMY_DATABASE_URI='sqlite://',
                               SQLALCHEMY_TRACK_MODIFICATIONS=False)
        db.init_app(self.app)
        self.app.register_blueprint(admin_bp)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.today = datetime.now(timezone(timedelta(hours=9))).date()
        self.user = User(name='Admin', role='admin')
        self.branch = Branch(name='Test')
        db.session.add_all([self.user, self.branch])
        db.session.flush()
        self.room = Room(branch_id=self.branch.id, name='101', status='occupied')
        db.session.add(self.room)
        db.session.flush()
        self.contract = Contract(user_id=self.user.id, room_id=self.room.id,
                                 start_date=self.today - timedelta(days=30),
                                 end_date=self.today + timedelta(days=90),
                                 status='terminate_requested', price=500000, deposit=500000,
                                 termination_effective_date=self.today + timedelta(days=30))
        db.session.add(self.contract)
        db.session.flush()
        self.req = Request(user_id=self.user.id, contract_id=self.contract.id,
                           type='termination', status='submitted', details='{}')
        db.session.add(self.req)
        db.session.commit()
        self.sms = patch('app.utils.sms_service.sms_service.send_sms', return_value=(True, 'test'))
        self.send_sms = self.sms.start()

    def tearDown(self):
        self.sms.stop()
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def approve(self, **data):
        # Invoke the real route body; authentication is outside this regression.
        from app.routes.admin import update_contract_status
        with self.app.test_request_context(json={'status': 'terminated', **data}):
            return update_contract_status.__wrapped__(self.user, self.contract.id)

    def test_admin_selected_future_date_keeps_room_occupied(self):
        target = self.today + timedelta(days=45)
        self.approve(termination_date=target.isoformat())
        self.assertEqual(self.contract.status, 'active')
        self.assertEqual(self.contract.auto_extend_status, 'will_terminate')
        self.assertEqual(self.contract.end_date, target)
        self.assertEqual(self.contract.termination_effective_date, target)
        self.assertEqual(self.room.status, 'occupied')
        self.assertEqual(self.req.status, 'done')
        self.assertEqual(json.loads(self.req.details)['termination_date'], target.isoformat())
        self.assertEqual(self.send_sms.call_count, 1)

    def test_legacy_approval_preserves_requested_date(self):
        target = self.contract.termination_effective_date
        self.approve()
        self.assertEqual(self.contract.status, 'active')
        self.assertEqual(self.contract.end_date, target)
        self.assertEqual(self.room.status, 'occupied')

    def test_last_use_day_stays_occupied_then_expires_next_day(self):
        self.approve(termination_date=self.today.isoformat())
        terminate_expired_contracts(self.app)
        self.assertEqual(self.contract.status, 'active')
        self.assertEqual(self.room.status, 'occupied')
        tomorrow = datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1)
        with patch('app.tasks.get_kst_now', return_value=tomorrow):
            terminate_expired_contracts(self.app)
        db.session.expire_all()
        self.assertEqual(self.contract.status, 'terminated')
        self.assertEqual(self.room.status, 'available')

    def test_explicit_immediate_termination_ends_today(self):
        self.approve(immediate=True)
        self.assertEqual(self.contract.status, 'terminated')
        self.assertEqual(self.contract.end_date, self.today)
        self.assertEqual(self.room.status, 'available')

    def test_invalid_dates_leave_contract_and_request_unchanged(self):
        for value in ['', '2026-02-30', 123]:
            response, status = self.approve(termination_date=value)
            self.assertEqual(status, 400)
            self.assertEqual(self.contract.status, 'terminate_requested')
            self.assertEqual(self.req.status, 'submitted')
        self.assertEqual(self.send_sms.call_count, 0)


if __name__ == '__main__':
    unittest.main()
