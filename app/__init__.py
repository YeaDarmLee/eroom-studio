from flask import Flask
from flask_cors import CORS
from config import config
from .extensions import db, migrate, scheduler
from flasgger import Swagger

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configure Upload Folder
    import os
    UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Debug: Print database URL
    print("=" * 80)
    print(">>> DATABASE URL:", app.config['SQLALCHEMY_DATABASE_URI'])
    print("=" * 80)

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    Swagger(app)

    # Initialize Scheduler
    from .tasks import terminate_expired_contracts, process_daily_sms_tasks
    scheduler.init_app(app)
    
    # Task 1: Auto-terminate expired contracts at 00:00
    @scheduler.task('cron', id='terminate_expired', hour=0, minute=0)
    def scheduled_termination():
        terminate_expired_contracts(app)

    # Task 2: Daily SMS Notifications at 09:00 KST
    @scheduler.task('cron', id='daily_sms_tasks', hour=9, minute=0)
    def scheduled_sms():
        process_daily_sms_tasks(app)
        
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
    
    @app.route('/health')
    def health():
        return {'status': 'ok'}

    return app
