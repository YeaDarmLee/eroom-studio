from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from functools import wraps
import jwt
from flask import current_app
from app.models.user import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['sub'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['sub'])
            
            if not current_user or current_user.role != 'admin':
                return jsonify({'message': 'Admin access required!'}), 403
                
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/mock-login', methods=['POST'])
def mock_login():
    """Mock login for test user (id=1)"""
    user = User.query.get(1)
    if not user:
        user = User(
            id=1,
            kakao_id='kakao_test_user_001',
            email='user@test.com',
            name='테스트유저',
            role='user',
            onboarding_status='existing_linked'
        )
        db.session.add(user)
        db.session.commit()
    
    access_token = AuthService.generate_token(user.id)
    return jsonify({
        'access_token': access_token,
        'token': access_token,  # For backward compatibility
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'onboarding_status': user.onboarding_status
        }
    })

@auth_bp.route('/mock-admin-login', methods=['POST'])
def mock_admin_login():
    """Mock login for admin user (id=2)"""
    admin = User.query.get(2)
    if not admin:
        admin = User(
            id=2,
            kakao_id='kakao_admin_001',
            email='admin@test.com',
            name='관리자',
            role='admin',
            onboarding_status='new_user_done'
        )
        db.session.add(admin)
        db.session.commit()
    
    access_token = AuthService.generate_token(admin.id)
    return jsonify({
        'access_token': access_token,
        'token': access_token,  # For backward compatibility
        'user': {
            'id': admin.id,
            'name': admin.name,
            'email': admin.email,
            'role': admin.role,
            'onboarding_status': admin.onboarding_status
        }
    })

@auth_bp.route('/email-register', methods=['POST'])
def email_register():
    """Register new user with email and password"""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', '')
    
    # Validation
    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message': 'Email already registered'}), 400
    
    # Create new user
    user = User(
        email=email,
        name=name,
        role='user',
        onboarding_status='new_user_done'
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    # Generate token
    access_token = AuthService.generate_token(user.id)
    
    return jsonify({
        'access_token': access_token,
        'token': access_token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'onboarding_status': user.onboarding_status
        }
    }), 201

@auth_bp.route('/email-login', methods=['POST'])
def email_login():
    """Login with email and password"""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    
    # Validation
    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400
    
    # Find user by email
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid email or password'}), 401
    
    # Generate token
    access_token = AuthService.generate_token(user.id)
    
    return jsonify({
        'access_token': access_token,
        'token': access_token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'onboarding_status': user.onboarding_status
        }
    })


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_me(current_user):
    return jsonify({
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
        'role': current_user.role,
        'onboarding_status': current_user.onboarding_status
    })

@auth_bp.route('/onboarding', methods=['POST'])
@token_required
def update_onboarding(current_user):
    data = request.get_json()
    user_type = data.get('type')
    
    if user_type == 'new':
        current_user.onboarding_status = 'new_user_done'
        db.session.commit()
        return jsonify({'message': 'Onboarding updated'})
    
    return jsonify({'message': 'Invalid type'}), 400
