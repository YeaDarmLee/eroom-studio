"""Settlement regressions use an isolated in-memory database, without the scheduler."""
import inspect
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from app.extensions import db
from app.models import Branch, Contract, Room, User
from app.models.request import Request
from app.routes.admin import get_contracts, get_contract_detail
from app.routes.contract import get_my_contracts, get_contract_view
from app.routes.request import create_request


class TerminationSettlementTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder=str(Path(__file__).resolve().parents[1] / 'app/templates'))
        self.app.config.update(TESTING=True, SECRET_KEY='test', SQLALCHEMY_DATABASE_URI='sqlite://',
                               SQLALCHEMY_TRACK_MODIFICATIONS=False)
        db.init_app(self.app)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.today = datetime.now(timezone(timedelta(hours=9))).date()
        self.end = self.today + timedelta(days=90)
        self.user = User(name='Test', role='admin')
        self.branch = Branch(name='Test')
        db.session.add_all([self.user, self.branch])
        db.session.flush()
        self.room = Room(branch_id=self.branch.id, name='101', price=500000, deposit=300000)
        db.session.add(self.room)
        db.session.flush()
        self.contract = Contract(user_id=self.user.id, room_id=self.room.id,
                                 start_date=self.today - timedelta(days=30), end_date=self.end,
                                 status='active', price=500000, deposit=300000)
        db.session.add(self.contract)
        db.session.commit()
        self.sms = patch('app.utils.sms_service.sms_service.send_sms', return_value=(True, 'test'))
        self.sms.start()

    def tearDown(self):
        self.sms.stop()
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def request_moveout(self, target):
        with self.app.test_request_context(json={'type': 'termination', 'contract_id': self.contract.id,
                                                'details': {'termination_date': target}}):
            return create_request.__wrapped__(self.user)

    def test_early_application_for_expiry_has_no_penalty(self):
        _, status = self.request_moveout(self.end.isoformat())
        self.assertEqual(status, 201)
        self.assertEqual(self.contract.penalty_amount_snapshot['penalty_amount'], 0)
        self.assertEqual(self.contract.termination_settlement['deposit_refund'], 300000)

    def test_one_day_early_caps_deduction_and_shows_excess(self):
        self.request_moveout((self.end - timedelta(days=1)).isoformat())
        settlement = self.contract.termination_settlement
        self.assertTrue(settlement['is_early_termination'])
        self.assertEqual(settlement['penalty_amount'], 500000)
        self.assertEqual(settlement['deposit_deduction'], 300000)
        self.assertEqual(settlement['deposit_refund'], 0)
        self.assertEqual(settlement['additional_payment'], 200000)
        self.assertEqual(self.contract.deposit, 300000)

    def test_indefinite_contract_has_no_fixed_term_penalty(self):
        self.contract.is_indefinite = True
        self.request_moveout((self.today + timedelta(days=30)).isoformat())
        self.assertEqual(self.contract.termination_settlement['penalty_amount'], 0)

    def test_approval_date_changes_recalculate_and_preserve_original_term(self):
        self.contract.apply_termination_request(self.end.isoformat())
        target = self.end - timedelta(days=10)
        self.contract.approve_termination(target)
        db.session.commit()
        db.session.expire_all()
        self.assertEqual(self.contract.end_date, target)
        self.assertEqual(self.contract.termination_settlement['original_end_date'], self.end.isoformat())
        self.assertEqual(self.contract.termination_settlement['deposit_deduction'], 300000)
        self.contract.approve_termination(self.end)
        self.assertEqual(self.contract.termination_settlement['deposit_deduction'], 0)

    def test_immediate_termination_preserves_deduction(self):
        self.contract.approve_termination(immediate=True)
        self.assertEqual(self.contract.termination_settlement['termination_date'], self.today.isoformat())
        self.assertEqual(self.contract.termination_settlement['deposit_deduction'], 300000)

    def test_cancellation_restores_term_and_removes_settlement(self):
        self.contract.apply_termination_request(self.today + timedelta(days=10), True)
        self.contract.approve_termination()
        self.contract.cancel_termination()
        self.assertEqual(self.contract.end_date, self.end)
        self.assertIsNone(self.contract.termination_settlement)
        self.assertIsNone(self.contract.penalty_amount_snapshot)
        self.assertFalse(self.contract.termination_confirmation_checked)

    def test_invalid_date_does_not_mutate_contract_or_create_request(self):
        for target in [None, '', '2026-02-30', 123, (self.contract.start_date - timedelta(days=1)).isoformat()]:
            _, status = self.request_moveout(target)
            self.assertEqual(status, 400)
            self.assertEqual(self.contract.status, 'active')
            self.assertIsNone(self.contract.penalty_amount_snapshot)
        self.assertEqual(Request.query.count(), 0)

    def test_zero_and_fallback_deposit(self):
        self.contract.deposit = 0
        self.contract.apply_termination_request(self.today)
        self.assertEqual(self.contract.termination_settlement['deposit_deduction'], 0)
        self.contract.deposit = None
        self.assertEqual(self.contract.termination_settlement['deposit_deduction'], self.room.deposit)
        self.contract.deposit = 700000
        self.assertEqual(self.contract.termination_settlement['deposit_refund'], 200000)

    def test_legacy_approved_contract_requires_review(self):
        self.contract.termination_effective_date = self.end
        self.contract.auto_extend_status = 'will_terminate'
        self.contract.penalty_amount_snapshot = {'penalty_amount': 500000}
        self.assertTrue(self.contract.termination_settlement['needs_review'])
        self.assertIsNone(self.contract.termination_settlement['deposit_refund'])

    def test_all_contract_apis_and_print_use_same_settlement(self):
        self.request_moveout((self.end - timedelta(days=1)).isoformat())
        with self.app.test_request_context():
            listing = inspect.unwrap(get_contracts)(self.user).get_json()[0]
            detail = inspect.unwrap(get_contract_detail)(self.user, self.contract.id).get_json()
            user_contract = inspect.unwrap(get_my_contracts)(self.user).get_json()[0]
            for payload in [listing, detail, user_contract]:
                self.assertEqual(payload['termination_settlement'], self.contract.termination_settlement)
            html = inspect.unwrap(get_contract_view)(self.user, self.contract.id).get_json()['html']
            self.assertIn('예상 차감 −300,000원', html)
            self.assertIn('반환 예정 0원', html)
            self.assertIn('보증금 초과 예상 위약금 200,000원', html)


if __name__ == '__main__':
    unittest.main()
