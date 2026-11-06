from flask import Flask
from flask_cors import CORS
from config import config
from .extensions import db, migrate, scheduler
from flasgger import Swagger

def create_app(config_name='default', overrides=None):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.config.update(overrides or {})
    app.config['APP_MODE'] = config_name
    if config_name in ('local', 'testing'):
        from sqlalchemy.engine import make_url
        if make_url(app.config['SQLALCHEMY_DATABASE_URI']).get_backend_name() != 'sqlite':
            raise RuntimeError('Local/test mode only permits an isolated SQLite database.')
        app.config.update(SMS_ENABLED=False, SCHEDULER_ENABLED=False)
    
    # Configure Upload Folder
    import os
    UPLOAD_FOLDER = (os.path.join(app.instance_path, 'local-uploads') if config_name in ('local', 'testing')
                     else os.path.join(app.root_path, 'static', 'uploads'))
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    Swagger(app)

    from werkzeug.exceptions import HTTPException
    from flask import jsonify, request
    @app.errorhandler(HTTPException)
    def api_error(error):
        if request.path.startswith(('/api/', '/admin/api/')):
            db.session.rollback()
            return jsonify({'message': error.description, 'error': error.description}), error.code
        return error

    # Initialize Scheduler
    from .tasks import terminate_expired_contracts, process_daily_sms_tasks
    if app.config['SCHEDULER_ENABLED']:
        scheduler.init_app(app)
    
    # Task 1: Auto-terminate expired contracts at 00:00
    def scheduled_termination():
        terminate_expired_contracts(app)

    # Task 2: Daily SMS Notifications at 09:00 KST
    def scheduled_sms():
        process_daily_sms_tasks(app)
        
    if app.config['SCHEDULER_ENABLED']:
        scheduler.add_job(id='terminate_expired', func=scheduled_termination, trigger='cron', hour=0, minute=0, replace_existing=True)
        scheduler.add_job(id='daily_sms_tasks', func=scheduled_sms, trigger='cron', hour=9, minute=0, replace_existing=True)
        scheduler.start()

    # Import models to ensure they are registered with SQLAlchemy
    from . import models

    # Register Blueprints
    from .routes.auth import auth_bp
    from .routes.public import public_bp
    from .routes.contract import contract_bp
    from .routes.request import request_bp
    from .routes.admin import admin_bp
    from .routes.main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(contract_bp)
    app.register_blueprint(request_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)

    if config_name in ('local', 'testing'):
        from flask import send_from_directory
        @app.route('/local-uploads/<path:filename>')
        def local_upload(filename):
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.context_processor
    def environment_context():
        return {'local_preview': config_name in ('local', 'testing')}
    
    @app.route('/health')
    def health():
        return {'status': 'ok', 'mode': config_name,
                'database_backend': db.engine.url.get_backend_name(),
                'sms_enabled': app.config['SMS_ENABLED'], 'scheduler_enabled': app.config['SCHEDULER_ENABLED']}

    return app
