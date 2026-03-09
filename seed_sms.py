import os
import sys
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

from app import create_app, db
from app.models.sms import SmsTemplate

def seed_sms_templates():
    app = create_app('default')
    with app.app_context():
        templates = [
            {
                'type': 'SIGNATURE_REQUESTED',
                'title': '(사용자) 서명 요청 안내',
                'content': '안녕하세요, {{user_name}}님. 신청하신 {{branch_name}} {{room_name}} 계약서가 준비되었습니다. 마이페이지에서 내용을 확인하시고 전자서명을 완료해주세요.'
            },
            {
                'type': 'SIGNATURE_COMPLETED',
                'title': '(관리자) 서명 완료 안내',
                'content': '[이룸스튜디오] {{user_name}}님의 {{branch_name}} {{room_name}} 계약 서명이 완료되었습니다. 최종 승인 상태로 전환되었습니다.'
            },
            {
                'type': 'SIGNATURE_REJECTED',
                'title': '(관리자) 서명 거절 안내',
                'content': '[이룸스튜디오] {{user_name}}님이 {{branch_name}} {{room_name}} 계약 서명을 거절하셨습니다. (사유: {{rejection_reason}})'
            },
            {
                'type': 'ADMIN_CONTRACT_APPLIED',
                'title': '(관리자) 신규 계약 신청 접수',
                'content': '[이룸스튜디오] 신규 계약 신청: {{user_name}}님이 {{branch_name}} {{room_name}} 계약을 신청했습니다.'
            },
            {
                'type': 'CONTRACT_REJECTED',
                'title': '(사용자) 계약/퇴실 신청 반려 안내',
                'content': '안녕하세요, {{user_name}}님. 신청하신 {{branch_name}} {{room_name}} 계약(또는 퇴실) 신청이 아래 사유로 반려되었습니다.\n\n사유: {{reject_reason}}\n\n자세한 사항은 이룸스튜디오 마이페이지를 확인해주세요.'
            },
            {
                'type': 'EXTEND_APPLIED',
                'title': '(관리자) 사용자 계약 연장 신청',
                'content': '[이룸스튜디오] 계약 연장 신청: {{user_name}}님이 {{branch_name}} {{room_name}} 계약을 {{extend_months}}개월 연장 신청했습니다.'
            },
            {
                'type': 'EXTEND_APPROVED',
                'title': '(사용자) 계약 연장 승인 안내',
                'content': '안녕하세요, {{user_name}}님. 신청하신 {{branch_name}} {{room_name}} 계약 연장이 승인되었습니다. 변경된 종료일: {{end_date}}'
            },
            {
                'type': 'EXTEND_REJECTED',
                'title': '(사용자) 계약 연장 반려 안내',
                'content': '안녕하세요, {{user_name}}님. 신청하신 {{branch_name}} {{room_name}} 계약 연장 신청이 아래 사유로 반려되었습니다.\n\n사유: {{reject_reason}}'
            },
            {
                'type': 'WELCOME_MESSAGE',
                'title': '(사용자) 입주 당일 환영/안내',
                'content': '안녕하세요, {{user_name}}님. 이룸스튜디오 {{branch_name}} {{room_name}} 입주를 환영합니다!\n\n오늘부터 정상적으로 시설 이용이 가능하시며, 비밀번호 등 입주 안내사항은 마이페이지 또는 별도 공지를 참조해주세요.',
                'schedule_offset': 0
            }
        ]

        for t_data in templates:
            ext_tmpl = SmsTemplate.query.filter_by(type=t_data['type']).first()
            if not ext_tmpl:
                new_tmpl = SmsTemplate(
                    type=t_data['type'],
                    title=t_data['title'],
                    content=t_data['content'],
                    is_active=True,
                    schedule_offset=t_data.get('schedule_offset', 0)
                )
                db.session.add(new_tmpl)
                print(f"Added template: {t_data['type']}")
            else:
                print(f"Template already exists: {t_data['type']}")
        
        db.session.commit()
        print("Done seeding SMS templates.")

if __name__ == '__main__':
    seed_sms_templates()
