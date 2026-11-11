"""Public home summaries must not mix monthly vacancies with other room types."""
import unittest
import re
from flask import template_rendered
from app import create_app
from app.extensions import db
from app.models import Branch, Room


class PublicHomeTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def render_home(self):
        captured = {}
        def record(sender, template, context, **extra):
            captured.update(context)
        with template_rendered.connected_to(record, self.app):
            response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        return response.get_data(as_text=True), captured

    def test_vacancies_and_start_price_only_include_available_monthly_rooms(self):
        branch = Branch(name='월간 비교점')
        db.session.add(branch)
        db.session.flush()
        for room_type, status, price in [
            ('monthly', 'available', 450000), ('monthly', 'available', 400000),
            ('monthly', 'occupied', 100000), ('monthly', 'reserved', 200000),
            ('monthly', 'maintenance', 50000), ('time_based', 'available', 10000),
            ('manager', 'available', 30000),
        ]:
            db.session.add(Room(branch_id=branch.id, name=f'{room_type}-{status}-{price}',
                                room_type=room_type, status=status, price=price))
        db.session.commit()
        html, context = self.render_home()
        self.assertEqual(context['branch_summaries'][branch.id],
                         {'available': 2, 'price_from': 400000})
        self.assertIn('월간 공실 2개', html)
        self.assertIn('400,000', html)

    def test_missing_and_zero_prices_are_not_advertised_as_free(self):
        branch = Branch(name='요금 확인점')
        db.session.add(branch)
        db.session.flush()
        for price in (None, 0):
            db.session.add(Room(branch_id=branch.id, name=str(price), room_type='monthly',
                                status='available', price=price))
        db.session.commit()
        html, context = self.render_home()
        self.assertIsNone(context['branch_summaries'][branch.id]['price_from'])
        self.assertIn('이용료는 지점에 문의해주세요', html)

    def test_empty_branch_and_missing_photo_have_useful_next_steps(self):
        db.session.add(Branch(name='사진 준비점', address='주소 확인'))
        db.session.commit()
        html, context = self.render_home()
        self.assertIsNone(context['featured_branch'])
        self.assertIn('현재 월간 공실이 없습니다', html)
        self.assertIn('지점·입주 예정 방 보기', html)
        self.assertNotIn('readdy.ai', html)
        self.assertIn('vacancy-sidebar', html)

    def test_no_branches_shows_contact_instead_of_admin_instruction(self):
        html, _ = self.render_home()
        self.assertIn('tel:01094885093', html)
        self.assertNotIn('관리자 페이지에서 지점을 등록', html)
        self.assertIn('https://eroom-studio.co.kr/', html)
        self.assertNotIn('vacancy-sidebar', html)

    def test_vacancy_shortcuts_match_counts_and_link_to_each_branch(self):
        available = Branch(name='공실 있는 지점')
        full = Branch(name='만실 지점')
        db.session.add_all([available, full])
        db.session.flush()
        db.session.add(Room(branch=available, name='월간', room_type='monthly', status='available', price=400000))
        db.session.add(Room(branch=full, name='시간제', room_type='time_based', status='available', price=10000))
        db.session.commit()
        html, _ = self.render_home()
        widget = html.split('id="vacancy-sidebar"', 1)[1].split('</aside>', 1)[0]
        self.assertIn(f'href="/branches/{available.id}"', widget)
        self.assertIn(f'href="/branches/{full.id}"', widget)
        self.assertIn('1개', widget)
        self.assertIn('만실', widget)

    def test_header_links_follow_home_section_order(self):
        html, _ = self.render_home()
        nav = html.split('aria-label="주요 메뉴"', 1)[1].split('</nav>', 1)[0]
        linked_sections = [href.split('#', 1)[1] for href in re.findall(r'href="([^\"]+)"', nav)]
        self.assertEqual(linked_sections, re.findall(r'<section id="([^\"]+)"', html))


if __name__ == '__main__':
    unittest.main()
