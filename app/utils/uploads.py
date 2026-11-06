from pathlib import Path
from flask import current_app
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
from uuid import uuid4

def save_image(file, category):
    extension = Path(secure_filename(file.filename or '')).suffix.lower()
    if extension not in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
        raise BadRequest('JPG, PNG, WEBP, GIF 이미지만 업로드할 수 있습니다.')
    root = Path(current_app.config.get('UPLOAD_FOLDER', str(Path(current_app.root_path)/'static/uploads')))
    folder = root/category
    folder.mkdir(parents=True, exist_ok=True)
    name = uuid4().hex + extension
    file.save(folder/name)
    return current_app.config.get('UPLOAD_URL_PREFIX', '/static/uploads') + '/' + category + '/' + name

def remove_image(url):
    prefix = current_app.config.get('UPLOAD_URL_PREFIX', '/static/uploads') + '/'
    if not url or not url.startswith(prefix):
        return
    root = Path(current_app.config.get('UPLOAD_FOLDER', str(Path(current_app.root_path)/'static/uploads'))).resolve()
    target = (root/url[len(prefix):]).resolve()
    if root not in target.parents:
        raise BadRequest('잘못된 이미지 경로입니다.')
    target.unlink(missing_ok=True)
