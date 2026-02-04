from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models.database import User, Announcement
from datetime import datetime, timedelta
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

from flask_login import login_required, current_user, login_user
from sqlalchemy import func

# ... (imports)

@admin_bp.route('/')
@login_required
@admin_required
def index():
    # Stats
    total_users = User.query.count()
    
    # Active users (last seen in 5 minutes)
    five_min_ago = datetime.utcnow() - timedelta(minutes=5)
    active_now = User.query.filter(User.last_seen >= five_min_ago).count()
    
    # Joined today
    today = datetime.utcnow().date()
    new_today = User.query.filter(User.created_at >= today).count()
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Growth Chart Data (Last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    
    # Query for daily signups
    # Note: SQLite vs Postgres date functions differ. Using Python for compatibility.
    users_last_30 = User.query.filter(User.created_at >= thirty_days_ago).all()
    
    dates = []
    counts = []
    
    # Dict to count per day
    daily_counts = {}
    current = thirty_days_ago
    while current <= today:
        daily_counts[current.strftime('%Y-%m-%d')] = 0
        current += timedelta(days=1)
        
    for user in users_last_30:
        d = user.created_at.date().strftime('%Y-%m-%d')
        if d in daily_counts:
            daily_counts[d] += 1
            
    dates = list(daily_counts.keys())
    counts = list(daily_counts.values())
    
    # Password Reset Requests
    reset_requests = User.query.filter_by(reset_requested=True).all()
    reset_count = len(reset_requests)
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_now=active_now,
                         new_today=new_today,
                         recent_users=recent_users,
                         chart_dates=dates,
                         chart_counts=counts,
                         reset_requests=reset_requests,
                         reset_count=reset_count)


@admin_bp.route('/users/<int:id>/approve-reset', methods=['POST'])
@login_required
@admin_required
def approve_reset(id):
    user = User.query.get_or_404(id)
    user.reset_approved = True
    user.reset_requested = False  # Clear request flag, but keep approved flag until they change it
    db.session.commit()
    flash(f'Password reset approved for {user.username}.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/users/<int:id>/reject-reset', methods=['POST'])
@login_required
@admin_required
def reject_reset(id):
    user = User.query.get_or_404(id)
    user.reset_requested = False
    user.reset_approved = False
    db.session.commit()
    flash(f'Password reset rejected for {user.username}.', 'info')
    return redirect(url_for('admin.index'))

@admin_bp.route('/users/<int:id>/impersonate', methods=['POST'])
@login_required
@admin_required
def impersonate_user(id):
    user = User.query.get_or_404(id)
    if user.is_admin:
        flash('Cannot impersonate another admin.', 'error')
        return redirect(url_for('admin.user_list'))
        
    login_user(user)
    flash(f'Logged in as {user.username}.', 'success')
    return redirect(url_for('dashboard.index'))

@admin_bp.route('/users')
@login_required
@admin_required
def user_list():
    query = request.args.get('q', '')
    if query:
        users = User.query.filter(User.username.ilike(f'%{query}%') | User.email.ilike(f'%{query}%')).all()
    else:
        users = User.query.order_by(User.id.desc()).all()
    return render_template('admin/users.html', users=users, query=query)

@admin_bp.route('/users/<int:id>/toggle-block', methods=['POST'])
@login_required
@admin_required
def toggle_block(id):
    user = User.query.get_or_404(id)
    if user == current_user:
        flash('You cannot block yourself.', 'error')
        return redirect(url_for('admin.user_list'))
        
    user.is_blocked = not user.is_blocked
    db.session.commit()
    status = "blocked" if user.is_blocked else "unblocked"
    flash(f'{user.username} has been {status}.', 'success')
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/users/<int:id>/warn', methods=['POST'])
@login_required
@admin_required
def warn_user(id):
    user = User.query.get_or_404(id)
    user.warning_count += 1
    db.session.commit()
    flash(f'Sent warning to {user.username}. Total: {user.warning_count}', 'warning')
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/announcement', methods=['POST'])
@login_required
@admin_required
def create_announcement():
    message = request.form.get('message')
    type = request.form.get('type')
    
    if message:
        # Deactivate old active announcements
        old = Announcement.query.filter_by(is_active=True).all()
        for a in old:
            a.is_active = False
            
        new_ann = Announcement(message=message, type=type, user_id=current_user.id)
        db.session.add(new_ann)
        db.session.commit()
        flash('Announcement published!', 'success')
        
    return redirect(url_for('admin.index'))

@admin_bp.route('/announcement/clear', methods=['POST'])
@login_required
@admin_required
def clear_announcement():
    # Deactivate all
    active = Announcement.query.filter_by(is_active=True).all()
    for a in active:
        a.is_active = False
    db.session.commit()
    flash('Announcement cleared.', 'success')
    return redirect(url_for('admin.index'))
