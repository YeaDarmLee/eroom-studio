from flask import Blueprint, render_template, redirect, url_for, request as flask_request
from app.models.branch import Branch, Room
from app.routes.auth import admin_required
import jwt
from flask import current_app
from app.models.user import User

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    branches = Branch.query.all()
    return render_template('public/index.html', branches=branches)

@main_bp.route('/branches/<int:branch_id>')
def branch_detail(branch_id):
    branch = Branch.query.get_or_404(branch_id)
    return render_template('public/branch_detail.html', branch=branch)

@main_bp.route('/rooms/<int:room_id>')
def room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    return render_template('public/room_detail.html', room=room)

@main_bp.route('/login')
def login():
    return render_template('user/login.html')

@main_bp.route('/register')
def register():
    return render_template('user/register.html')

@main_bp.route('/my/room')
def dashboard():
    return render_template('user/dashboard.html')
@main_bp.route('/onboarding')
def onboarding():
    return render_template('user/onboarding.html')

@main_bp.route('/requests/new')
def new_request():
    return render_template('user/request_form.html')

@main_bp.route('/admin')
def admin_dashboard():
    # Auth will be handled by frontend JavaScript
    return render_template('admin/dashboard.html')
