"""
Database utility functions for handling connection issues
"""
from functools import wraps
from time import sleep
from sqlalchemy.exc import OperationalError, DBAPIError
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def db_retry(max_retries=3, delay=1):
    """
    데코레이터: 데이터베이스 연결 오류 시 재시도
    
    Args:
        max_retries: 최대 재시도 횟수
        delay: 재시도 간 대기 시간 (초)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DBAPIError) as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"DB operation failed after {max_retries} retries: {str(e)}")
                        raise
                    
                    logger.warning(f"DB connection error (attempt {retries}/{max_retries}): {str(e)}")
                    logger.warning(f"Retrying in {delay} seconds...")
                    sleep(delay)
                    
                    # SQLAlchemy 세션을 명시적으로 제거하여 새로운 연결 시도
                    from app.extensions import db
                    db.session.remove()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
