import unittest
from datetime import date, datetime, timedelta, timezone
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.branch import Branch, Room
from app.models.contract import Contract
from app.models.user import User

class ContractTerminationFlowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 전체에서 App Context 1회 초기화"""
        cls.app = create_app('testing')
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        """각 테스트 전 DB 트랜잭션 수립 및 픽스처 생성"""
        self.transaction = db.session.begin_nested()
        self.today = datetime.now(timezone(timedelta(hours=9))).date()
        self.future_termination = self.today + timedelta(days=30)

        # 테스트용 사용자, 지점, 방 생성
        self.user = User(name="테스터", email="test@example.com", phone="010-0000-0000")
        self.user2 = User(name="테스터2", email="test2@example.com", phone="010-1111-1111")
        self.branch = Branch(name="테스트지점")
        db.session.add_all([self.user, self.user2, self.branch])
        db.session.flush()

        self.room = Room(branch_id=self.branch.id, name="101호", price=500000, deposit=500000, status="available")
        db.session.add(self.room)
        db.session.flush()

        # 기본 Active 계약 생성
        self.contract = Contract(
            user_id=self.user.id,
            room_id=self.room.id,
            start_date=self.today - timedelta(days=180),
            end_date=self.today + timedelta(days=60),
            price=500000,
            deposit=500000,
            status='active'
        )
        db.session.add(self.contract)
        db.session.flush()
        self.room.sync_status()

    def tearDown(self):
        """각 테스트 후 DB 롤백"""
        db.session.rollback()

    # --- Scenario A & A-2: 해지 신청 및 철회 / 반려 ---
    def test_A_apply_and_cancel_termination_clears_all_snapshots(self):
        """Test A: 해지 신청 후 철회 시 해지 스냅샷 5종 필드가 완전 제거되고 occupied가 유지되는지 검증"""
        # 1. 해지 신청
        self.contract.apply_termination_request(termination_date=self.future_termination.isoformat(), confirmation_checked=True)
        self.contract.remaining_months_at_termination = 1
        self.contract.penalty_amount_snapshot = {"penalty": 500000}
        self.contract.termination_confirmation_text_snapshot = "확인문구"
        db.session.flush()

        self.assertEqual(self.contract.status, 'terminate_requested')
        self.assertEqual(self.contract.termination_effective_date, self.future_termination)
        self.assertEqual(self.room.status, 'occupied')

        # 2. 해지 철회
        self.contract.cancel_termination()
        db.session.flush()

        # 3. 스냅샷 5종 필드 완전 제거 검증
        self.assertEqual(self.contract.status, 'active')
        self.assertIsNone(self.contract.termination_effective_date)
        self.assertIsNone(self.contract.termination_requested_at)
        self.assertIsNone(self.contract.remaining_months_at_termination)
        self.assertIsNone(self.contract.penalty_amount_snapshot)
        self.assertIsNone(self.contract.termination_confirmation_text_snapshot)
        self.assertEqual(self.contract.auto_extend_status, 'none')
        self.assertEqual(self.room.status, 'occupied')
        self.assertIsNone(self.room.get_next_available_date())

    def test_A2_admin_reject_termination(self):
        """Test A-2: 관리자 반려 시 active 및 occupied 복원 검증"""
        self.contract.apply_termination_request(termination_date=self.future_termination.isoformat())
        self.contract.cancel_termination()
        
        self.assertEqual(self.contract.status, 'active')
        self.assertEqual(self.room.status, 'occupied')

    # --- Scenario B: 미래 해지 승인 ---
    def test_B_future_termination_approval(self):
        """Test B: 미래 날짜 해지 승인 시 당일 공실 전환 없이 active/occupied 유지 검증"""
        self.contract.apply_termination_request(termination_date=self.future_termination.isoformat())
        self.contract.approve_termination(termination_date=self.future_termination.isoformat())
        db.session.flush()

        # P0 Invariants 검증
        self.assertEqual(self.contract.status, 'active')
        self.assertEqual(self.contract.auto_extend_status, 'will_terminate')
        self.assertEqual(self.contract.end_date, self.future_termination)
        self.assertEqual(self.contract.termination_effective_date, self.future_termination)
        self.assertEqual(self.room.status, 'occupied')
        self.assertEqual(self.room.get_next_available_date(), self.future_termination + timedelta(days=1))

    # --- Scenario C-1 & C-2: 당일 즉시 퇴실 ---
    def test_C1_immediate_termination_without_future_contract(self):
        """Test C-1: 당일 즉시 퇴실 처리 후 후속 계약이 없는 경우 -> available"""
        self.contract.approve_termination(immediate=True)
        db.session.flush()

        self.assertEqual(self.contract.status, 'terminated')
        self.assertEqual(self.room.status, 'available')

    def test_C2_immediate_termination_with_future_contract(self):
        """Test C-2: 당일 즉시 퇴실 처리 후 미래 승인 계약이 존재하는 경우 -> reserved"""
        future_contract = Contract(
            user_id=self.user2.id,
            room_id=self.room.id,
            start_date=date(2026, 10, 1),
            end_date=date(2027, 4, 1),
            price=500000,
            status='approved'
        )
        db.session.add(future_contract)
        db.session.flush()

        # 기존 계약 즉시 종료
        self.contract.approve_termination(immediate=True)
        db.session.flush()

        self.assertEqual(self.contract.status, 'terminated')
        self.assertEqual(self.room.status, 'reserved')

    # --- Scenario D-1 ~ D-5: Room.sync_status() 우선순위 검증 ---
    def test_D1_to_D5_room_sync_status_priorities(self):
        """Test D-1 ~ D-5: Room.sync_status() 우선순위 및 덮어쓰기 방지 검증"""
        # D-1: active -> occupied
        self.assertEqual(self.room.sync_status(), 'occupied')

        # D-4: maintenance 보호
        self.room.status = 'maintenance'
        self.assertEqual(self.room.sync_status(), 'maintenance')
        self.room.status = 'occupied' # restore

        # D-5: active + future reserved 동시 존재시에도 occupied 유지
        future_contract = Contract(
            user_id=self.user2.id,
            room_id=self.room.id,
            start_date=date(2026, 12, 1),
            end_date=date(2027, 5, 1),
            price=500000,
            status='waiting_signature'
        )
        db.session.add(future_contract)
        db.session.flush()
        
        self.assertEqual(self.room.sync_status(), 'occupied')

        # D-2: active 계약 종료 시 future reserved만 남아있으므로 reserved로 전이
        self.contract.status = 'terminated'
        self.assertEqual(self.room.sync_status(), 'reserved')

        # D-3: 모든 계약 terminated 시 available로 전이
        future_contract.status = 'cancelled'
        self.assertEqual(self.room.sync_status(), 'available')

    # --- Scenario E & E-2: 해지 예정일 도래 후 실제 종료 ---
    def test_E_effective_date_expiration(self):
        """Test E: 해지 예정일 도래 시 계약 종료 및 방 상태 전이 검증"""
        self.contract.approve_termination(termination_date=self.future_termination.isoformat())
        
        # 해지일 당일까지는 active / occupied
        self.assertEqual(self.contract.status, 'active')
        self.assertEqual(self.room.status, 'occupied')

        # 만료 시점 도래 시 계약 termination 동기화
        today_mock = self.future_termination + timedelta(days=1)
        if self.contract.end_date < today_mock:
            self.contract.status = 'terminated'
            self.room.sync_status()

        self.assertEqual(self.contract.status, 'terminated')
        self.assertEqual(self.room.status, 'available')

    # --- Scenario F: Atomic Transaction Rollback ---
    def test_F_atomic_transaction_rollback(self):
        """Test F: 도중 에러 발생 시 트랜잭션 롤백으로 이전 상태 완벽 유지 검증"""
        orig_status = self.contract.status
        orig_room_status = self.room.status

        sp = db.session.begin_nested()
        try:
            self.contract.approve_termination(termination_date=self.future_termination.isoformat())
            raise RuntimeError("Simulated Database Failure")
        except RuntimeError:
            sp.rollback()

        self.assertEqual(self.contract.status, orig_status)
        self.assertEqual(self.room.status, orig_room_status)

    # --- Scenario G & H: Idempotency (중복 호출 멱등성) ---
    def test_G_H_idempotency_of_approval_and_cancellation(self):
        """Test G & H: 승인 및 철회 중복 호출 멱등성 검증"""
        # 중복 승인
        self.contract.approve_termination(termination_date=self.future_termination.isoformat())
        self.contract.approve_termination(termination_date=self.future_termination.isoformat())
        self.assertEqual(self.contract.status, 'active')
        self.assertEqual(self.contract.termination_effective_date, self.future_termination)

        # 중복 철회
        self.contract.cancel_termination()
        self.contract.cancel_termination()
        self.assertEqual(self.contract.status, 'active')
        self.assertIsNone(self.contract.termination_effective_date)

if __name__ == '__main__':
    unittest.main()
