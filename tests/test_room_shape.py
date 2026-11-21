"""Non-rectangular rooms: shape is validated, saved and exposed to the public plan."""
import unittest
from app import create_app
from app.extensions import db
from app.models import Branch, Room
from app.models.user import User
from app.routes.admin import admin_bp  # noqa: F401  (ensure blueprint import works)


class RoomShapeTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()
        b = Branch(name='공개점', is_published=True)
        db.session.add(b)
        db.session.flush()
        self.room = Room(branch_id=b.id, name='2호', floor='1F', room_type='monthly', status='available', price=1)
        db.session.add(self.room)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_shape_default_none_and_public_api_exposes_it(self):
        self.assertIsNone(self.room.shape)
        self.room.shape = '35% 0, 100% 0, 100% 100%, 0 100%, 0 35%'
        db.session.commit()
        data = self.client.get(f'/api/public/branches/{self.room.branch_id}').get_json()
        self.assertEqual(data['rooms_by_floor']['1F'][0]['shape'], '35% 0, 100% 0, 100% 100%, 0 100%, 0 35%')


if __name__ == '__main__':
    unittest.main()
