"""
계약 매핑 서비스: 회원가입 시 미매핑 계약을 자동으로 매핑하는 로직
"""
from app.extensions import db
from app.models.contract import Contract
from app.models.user import User
from sqlalchemy import or_

class ContractMappingService:
    @staticmethod
    def map_contracts_to_user(user):
        """
        회원가입한 사용자에게 미매핑 계약을 자동으로 매핑
        
        Args:
            user: User 객체
            
        Returns:
            매핑된 계약 수
        """
        if not user:
            return 0
        
        # 전화번호나 이메일로 미매핑 계약 찾기
        unmapped_contracts = Contract.query.filter(
            Contract.user_id.is_(None),
            or_(
                Contract.temp_user_phone == user.phone if user.phone else False,
                Contract.temp_user_email == user.email if user.email else False
            )
        ).all()
        
        mapped_count = 0
        for contract in unmapped_contracts:
            # 매핑 전에 확인: 전화번호나 이메일이 일치하는지
            phone_match = user.phone and contract.temp_user_phone == user.phone
            email_match = user.email and contract.temp_user_email == user.email
            
            if phone_match or email_match:
                contract.user_id = user.id
                mapped_count += 1
                print(f"✅ 계약 #{contract.id}를 사용자 #{user.id}({user.name})에게 매핑")
        
        if mapped_count > 0:
            db.session.commit()
            print(f"🎉 총 {mapped_count}개의 계약이 매핑되었습니다!")
        
        return mapped_count
    
    @staticmethod
    def get_unmapped_contracts(phone=None, email=None):
        """
        특정 전화번호나 이메일로 미매핑 계약 조회
        
        Args:
            phone: 전화번호
            email: 이메일
            
        Returns:
            미매핑 계약 리스트
        """
        query = Contract.query.filter(Contract.user_id.is_(None))
        
        conditions = []
        if phone:
            conditions.append(Contract.temp_user_phone == phone)
        if email:
            conditions.append(Contract.temp_user_email == email)
        
        if conditions:
            query = query.filter(or_(*conditions))
        
        return query.all()
    
    @staticmethod
    def manual_map_contract(contract_id, user_id):
        """
        관리자가 수동으로 계약을 사용자에게 매핑
        
        Args:
            contract_id: 계약 ID
            user_id: 사용자 ID
            
        Returns:
            성공 여부
        """
        contract = Contract.query.get(contract_id)
        user = User.query.get(user_id)
        
        if not contract or not user:
            return False
        
        contract.user_id = user_id
        db.session.commit()
        
        return True
    
    @staticmethod
    def get_all_unmapped_contracts():
        """
        모든 미매핑 계약 조회
        
        Returns:
            미매핑 계약 리스트
        """
        return Contract.query.filter(Contract.user_id.is_(None)).all()
