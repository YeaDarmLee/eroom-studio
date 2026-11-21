"""Unpublished branches must be hidden from every public surface."""
import unittest
from app import create_app
from app.extensions import db
from app.models import Branch, Room


class BranchPublishTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.pub = Branch(name='공개점', is_published=True)
        self.hid = Branch(name='비공개점', is_published=False)
        db.session.add_all([self.pub, self.hid])
        db.session.flush()
        self.hid_room = Room(branch_id=self.hid.id, name='101', room_type='monthly', status='available', price=100000)
        db.session.add(self.hid_room)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_default_is_published(self):
        b = Branch(name='기본')
        db.session.add(b)
        db.session.commit()
        self.assertTrue(b.is_published)

    def test_public_pages_and_api_hide_unpublished(self):
        self.assertIn('공개점', self.client.get('/').get_data(as_text=True))
        self.assertNotIn('비공개점', self.client.get('/').get_data(as_text=True))
        names = [b['name'] for b in self.client.get('/api/public/branches').get_json()]
        self.assertEqual(names, ['공개점'])
        for url in (f'/branches/{self.hid.id}', f'/rooms/{self.hid_room.id}',
                    f'/api/public/branches/{self.hid.id}', f'/api/public/branches/{self.hid.id}/rooms',
                    '/api/public/branches/비공개/rooms-status'):
            self.assertEqual(self.client.get(url).status_code, 404, url)
        self.assertEqual(self.client.get(f'/branches/{self.pub.id}').status_code, 200)


if __name__ == '__main__':
    unittest.main()
