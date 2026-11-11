from flask import Blueprint, render_template, redirect, url_for, request as flask_request
from app.models.branch import Branch, Room
from app.routes.auth import admin_required
from app.utils.db_utils import db_retry
from app.utils.branch_utils import sort_branches
import jwt
from flask import current_app
from app.models.user import User

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@db_retry(max_retries=3, delay=1)
def index():
    branches = sort_branches(Branch.query.all())
    from sqlalchemy import func, case
    from app.extensions import db

    # Summaries describe currently available monthly rooms, not future vacancies.
    rows = db.session.query(
        Room.branch_id, func.count(Room.id),
        func.min(case((Room.price > 0, Room.price), else_=None)),
    ).filter(Room.room_type == 'monthly', Room.status == 'available').group_by(Room.branch_id).all()
    summaries = {branch_id: {'available': count, 'price_from': price}
                 for branch_id, count, price in rows}
    featured_branch = next((branch for branch in branches if branch.image_url), None)
    return render_template('public/index.html', branches=branches,
                           branch_summaries=summaries, featured_branch=featured_branch)

@main_bp.route('/about')
def about():
    return render_template('public/about.html')

@main_bp.route('/branches/<int:branch_id>')
@db_retry(max_retries=3, delay=1)
def branch_detail(branch_id):
    branch = Branch.query.get_or_404(branch_id)
    return render_template('public/branch_detail.html', branch=branch)

@main_bp.route('/rooms/<int:room_id>')
@db_retry(max_retries=3, delay=1)
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
@main_bp.route('/onboarding/link')
def onboarding_link():
    return redirect('/my/room#requests')

@main_bp.route('/onboarding')
def onboarding():
    return render_template('user/onboarding.html')

@main_bp.route('/requests/new')
def new_request():
    return redirect('/my/room#requests')

@main_bp.route('/terms')
def terms():
    return render_template('public/terms.html')

@main_bp.route('/privacy')
def privacy():
    return render_template('public/privacy.html')

@main_bp.route('/admin')
def admin_dashboard():
    return render_template('admin/dashboard.html')
