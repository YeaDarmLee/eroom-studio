"""Preview the local UI with public branch data, without changing either database.

Run from the project root. Browse http://127.0.0.1:5058/.
Only public GET endpoints are read; SQLite stays in memory and delivery is disabled.
The snapshot is for visual review, not a production booking environment.
Future move-in dates backed by private contracts are not reproduced here.
"""
import json
import sys
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from app.extensions import db
from app.models import Branch, Room
from app.models.branch import BranchImage, BranchFloor, RoomImage

ORIGIN = 'https://eroom-studio.co.kr'


def public_json(path):
    with urlopen(ORIGIN + path, timeout=20) as response:
        return json.load(response)


def absolute(path):
    return ORIGIN + path if path and path.startswith('/') else path


def preview_app():
    app = create_app('local', {'SQLALCHEMY_DATABASE_URI': 'sqlite://'})
    with app.app_context():
        db.create_all()
        for data in public_json('/api/public/branches'):
            branch = Branch(id=data['id'], name=data['name'], address=data.get('address'),
                            description=data.get('description'), image_url=absolute(data.get('image_url')))
            db.session.add(branch)
            detail = public_json(f'/api/public/branches/{branch.id}')
            for floor, rooms in detail.get('rooms_by_floor', {}).items():
                for room in rooms:
                    fields = {key: room.get(key) for key in ('id', 'name', 'room_type', 'price', 'deposit',
                              'status', 'description', 'area', 'position_x', 'position_y', 'width', 'height')}
                    model = Room(branch=branch, floor=floor, **fields)
                    db.session.add(model)
                    for photo in room.get('images', []):
                        db.session.add(RoomImage(room=model, image_url=absolute(photo['url'])))
            if branch.image_url:
                db.session.add(BranchImage(branch=branch, image_url=branch.image_url))
            for floor, photo in detail.get('floor_plans', {}).items():
                db.session.add(BranchFloor(branch=branch, floor=floor, floor_plan_image=absolute(photo)))
        db.session.commit()
        print(f'Public snapshot: {Branch.query.count()} branches; memory SQLite; SMS/scheduler OFF', flush=True)
    return app


if __name__ == '__main__':
    preview_app().run(host='127.0.0.1', port=5058, use_reloader=False)
