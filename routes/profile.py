"""
Profile Routes - User profile management for IIUM students
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models.database import Profile, KULLIYYAH_CHOICES, PROGRAM_LEVELS

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


@profile_bp.route('/', methods=['GET'])
@login_required
def view_profile():
    """View user profile"""
    profile = current_user.profile
    return render_template('profile.html', 
                         profile=profile,
                         kulliyyahs=KULLIYYAH_CHOICES,
                         levels=PROGRAM_LEVELS)


@profile_bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    """First-time profile setup"""
    if current_user.profile:
        return redirect(url_for('profile.view_profile'))
    
    if request.method == 'POST':
        profile = Profile(
            user_id=current_user.id,
            matric_number=request.form.get('matric_number', '').strip().upper(),
            kulliyyah=request.form.get('kulliyyah'),
            program_name=request.form.get('program_name', '').strip(),
            program_level=request.form.get('program_level'),
            current_semester=int(request.form.get('current_semester', 1)),
            intake_year=int(request.form.get('intake_year')) if request.form.get('intake_year') else None,
            phone=request.form.get('phone', '').strip()
        )
        
        db.session.add(profile)
        db.session.commit()
        
        flash('Profile created successfully! Welcome to SAS! 🎓', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('profile_setup.html',
                         kulliyyahs=KULLIYYAH_CHOICES,
                         levels=PROGRAM_LEVELS)


@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """Edit existing profile"""
    profile = current_user.profile
    
    if not profile:
        return redirect(url_for('profile.setup'))
    
    if request.method == 'POST':
        profile.matric_number = request.form.get('matric_number', '').strip().upper()
        profile.kulliyyah = request.form.get('kulliyyah')
        profile.program_name = request.form.get('program_name', '').strip()
        profile.program_level = request.form.get('program_level')
        profile.current_semester = int(request.form.get('current_semester', 1))
        profile.intake_year = int(request.form.get('intake_year')) if request.form.get('intake_year') else None
        profile.expected_graduation = request.form.get('expected_graduation', '').strip()
        profile.phone = request.form.get('phone', '').strip()
        
        db.session.commit()
        
        flash('Profile updated successfully! ✅', 'success')
        return redirect(url_for('profile.view_profile'))
    
    return render_template('profile.html',
                         profile=profile,
                         kulliyyahs=KULLIYYAH_CHOICES,
                         levels=PROGRAM_LEVELS,
                         editing=True)
