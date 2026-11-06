import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///eroom.db'
    
    # Aligo SMS Configuration
    ALIGO_API_KEY = os.environ.get('ALIGO_API_KEY')
    ALIGO_USER_ID = os.environ.get('ALIGO_USER_ID')
    ALIGO_SENDER = os.environ.get('ALIGO_SENDER')
    SMS_ENABLED = True
    SCHEDULER_ENABLED = True
    SCHEDULER_TIMEZONE = 'Asia/Seoul'
    
    # MySQL 연결 끊김 문제 해결을 위한 설정
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,          # 연결 사용 전 ping으로 상태 확인
        'pool_recycle': 280,            # 280초(약 4.7분)마다 연결 재생성 (MySQL wait_timeout 문제 방지)
        'pool_size': 10,                # 연결 풀 크기
        'max_overflow': 20,             # 풀 크기를 초과할 수 있는 최대 연결 수
        'pool_timeout': 30,             # 연결을 얻기 위한 대기 시간 (초)
        'echo_pool': True,              # 연결 풀 이벤트 로깅 (디버깅용)
        'connect_args': {
            'connect_timeout': 10,      # MySQL 연결 타임아웃 (초)
            'autocommit': False,        # 명시적 트랜잭션 관리
            'charset': 'utf8mb4'        # UTF-8 문자셋
        }
    }

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class LocalConfig(Config):
    """Explicitly isolated preview; never inherit DATABASE_URL or delivery settings."""
    DEBUG = False
    TEMPLATES_AUTO_RELOAD = True
    SECRET_KEY = 'local-preview-only-not-valid-in-production'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///local-preview.sqlite3'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    SMS_ENABLED = False
    SCHEDULER_ENABLED = False
    ALIGO_API_KEY = None
    ALIGO_USER_ID = None
    ALIGO_SENDER = None
    UPLOAD_URL_PREFIX = '/local-uploads'

class TestingConfig(LocalConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'local': LocalConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
