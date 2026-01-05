from flask import Blueprint, request, jsonify, redirect
from app.services.auth_service import AuthService
from functools import wraps
import jwt
import os
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
@auth_bp.route('/kakao/login', methods=['GET'])
def kakao_login():
    """Redirect to Kakao Login Page"""
    client_id = os.environ.get('KAKAO_CLIENT_ID')
    redirect_uri = os.environ.get('KAKAO_REDIRECT_URI', 'http://localhost:5000/api/auth/kakao/callback')
    
    if not client_id:
        return jsonify({'message': 'Kakao Client ID not configured'}), 500
        
    kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
    return jsonify({'url': kakao_auth_url})

@auth_bp.route('/kakao/callback', methods=['GET'])
def kakao_callback():
    """Handle Kakao OAuth Callback"""
    code = request.args.get('code')
    
    if not code:
        return jsonify({'message': 'Authorization code is missing'}), 400
        
    client_id = os.environ.get('KAKAO_CLIENT_ID')
    redirect_uri = os.environ.get('KAKAO_REDIRECT_URI', 'http://localhost:5000/api/auth/kakao/callback')
    
    if not client_id:
        return jsonify({'message': 'Kakao Client ID not configured'}), 500
    
    # 1. Get Access Token
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'code': code
    }
    
    try:
        import requests
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            return jsonify({'message': 'Failed to get access token from Kakao', 'error': token_json}), 400
            
        access_token = token_json['access_token']
        
        # 2. Get User Info
        user_url = "https://kapi.kakao.com/v2/user/me"
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(user_url, headers=headers)
        user_info = user_response.json()
        
        kakao_id = str(user_info.get('id'))
        properties = user_info.get('properties', {})
        kakao_account = user_info.get('kakao_account', {})
        
        nickname = properties.get('nickname', f'User_{kakao_id}')
        email = kakao_account.get('email', f'{kakao_id}@kakao.placeholder')
        
        # 3. Create or Get User
        user = User.query.filter_by(kakao_id=kakao_id).first()
        
        if not user:
            # Check if email exists (conflict resolution or merge?)
            # For now, if email exists but no kakao_id, we just link it if we trust the email?
            # Or just create a new user unique to Kakao
             user = User(
                kakao_id=kakao_id,
                name=nickname,
                email=email,
                role='user',
                onboarding_status='new_user_done' # Assumption
            )
             db.session.add(user)
             db.session.commit()
        
        # 4. Generate App Token
        app_token = AuthService.generate_token(user.id)
        
        # Redirect to frontend with token
        # Since this is a redirect callback, we can't return JSON to the browser directly if we want to set local storage.
        # Common pattern: Redirect to a frontend page with the token in URL fragment or query param
        frontend_redirect_url = f"/login?token={app_token}"
        return redirect(frontend_redirect_url)
        
    except Exception as e:
        return jsonify({'message': 'Kakao Login Failed', 'error': str(e)}), 500
