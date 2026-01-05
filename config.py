import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///eroom.db'
    
    # MySQL 연결 끊김 문제 해결을 위한 설정
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # 연결 사용 전 ping으로 상태 확인
        'pool_recycle': 3600,   # 1시간마다 연결 재생성 (MySQL wait_timeout보다 짧게)
        'pool_size': 10,        # 연결 풀 크기
        'max_overflow': 20,     # 풀 크기를 초과할 수 있는 최대 연결 수
    }

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
