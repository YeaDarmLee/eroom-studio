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
        회원가입하거나 정보를 수정한 사용자에게 계약을 자동으로 매핑
        1. 미매핑 계약(user_id가 None) 중 전화번호나 이메일이 일치하는 건 매핑
        2. 임시 사용자(email이 'temp_'로 시작)에게 매핑된 계약 중 전화번호가 일치하는 건 현재 사용자로 재매핑
        """
        if not user:
            return 0
        
        mapped_count = 0
        
        # 1. 미매핑 계약 매핑
        unmapped_contracts = Contract.query.filter(
            Contract.user_id.is_(None),
            or_(
                Contract.temp_user_phone == user.phone if user.phone else False,
                Contract.temp_user_email == user.email if user.email else False
            )
        ).all()
        
        for contract in unmapped_contracts:
            contract.user_id = user.id
            mapped_count += 1
            print(f"✅ 미매핑 계약 #{contract.id}를 사용자 #{user.id}({user.name})에게 매핑")

        # 2. 임시 사용자 계정의 계약 가로채기 (재매핑)
        # 현재 사용자의 전화번호가 있고, 그 전화번호를 가진 임시 계정이 있다면
        if user.phone:
            placeholder_users = User.query.filter(
                User.phone == user.phone,
                User.email.like('temp_%'),
                User.id != user.id
            ).all()
            
            for pu in placeholder_users:
                # 이 임시 계정에 연결된 계약들을 현재 사용자에게 옮김
                pu_contracts = Contract.query.filter_by(user_id=pu.id).all()
                for c in pu_contracts:
                    c.user_id = user.id
                    mapped_count += 1
                    print(f"🔄 임시 사용자 #{pu.id}의 계약 #{c.id}를 실제 사용자 #{user.id}에게 재매핑")
                
                # 임시 사용자의 요청(Request)들도 옮겨줌
                from app.models.request import Request
                pu_requests = Request.query.filter_by(user_id=pu.id).all()
                for r in pu_requests:
                    r.user_id = user.id
                
                # 중복 방지를 위해 임시 계정의 전화번호 제거 (또는 계정 삭제 고민 필요)
                # 여기서는 번호만 제거하여 중복 매핑 방지
                pu.phone = f"old_{pu.phone}_{pu.id}"
        
        if mapped_count > 0:
            db.session.commit()
            print(f"🎉 총 {mapped_count}개의 계약이 처리되었습니다!")
        
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
