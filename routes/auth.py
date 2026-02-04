"""
Authentication Routes for Student Assistant System
Handles user signup, login, and logout functionality
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from models.database import User
from app import db

# Create blueprint
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    User registration page.
    
    GET: Display signup form
    POST: Process registration
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken. Please choose another.')
        
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered. Please login instead.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/signup.html', 
                                 username=username, 
                                 email=email)
        
        # Create new user
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            print(f"Signup error: {e}")
    
    return render_template('auth/signup.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login page.
    
    GET: Display login form
    POST: Authenticate user
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False) == 'on'
        
        # Validation
        if not email or not password:
            flash('Please enter both username/email and password.', 'error')
            return render_template('auth/login.html', email=email)
        
        # Find user by email OR username
        from sqlalchemy import or_
        user = User.query.filter(or_(User.email == email, User.username == email)).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid email or password.', 'error')
            return render_template('auth/login.html', email=email)
        
        # Check if blocked
        if user.is_blocked:
            flash('Your account has been suspended by an administrator.', 'error')
            return render_template('auth/login.html', email=email)
        
        # Login user
        login_user(user, remember=remember)
        session.permanent = remember
        
        flash(f'Welcome back, {user.username}!', 'success')
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """
    Logout current user and clear session.
    """
    username = current_user.username
    logout_user()
    session.clear()
    
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        
        user = User.query.filter((User.email == identifier) | (User.username == identifier)).first()
        if user:
            user.reset_requested = True
            db.session.commit()
            flash('Password reset requested! Please wait for Admin approval.', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('User not found.', 'error')
            
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('User not found.', 'error')
        elif not user.reset_approved:
            flash('Password reset has NOT been approved by Admin yet.', 'warning')
        elif password != confirm:
            flash('Passwords do not match.', 'error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
        else:
            # Success
            user.set_password(password)
            user.reset_approved = False  # Reset flags
            user.reset_requested = False
            db.session.commit()
            flash('Password changed successfully! You can now login.', 'success')
            return redirect(url_for('auth.login'))
            
    return render_template('auth/reset_password.html')
