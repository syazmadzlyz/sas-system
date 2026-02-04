"""
Attendance Routes for Student Assistant System
Handles attendance tracking and bar prediction
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.database import Attendance, Subject
from app import db

# Create blueprint
attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
def index():
    """
    Attendance calculator page.
    
    GET: Display attendance form and history
    POST: Calculate and save attendance
    """
    # Get existing attendance records
    attendances = Attendance.query.filter_by(user_id=current_user.id)\
        .order_by(Attendance.updated_at.desc()).all()
    
    # Get user's subjects for dropdown
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    
    result = None
    
    if request.method == 'POST':
        subject_name = request.form.get('subject_name', '').strip()
        total_weeks = request.form.get('total_weeks', 14, type=int)
        classes_per_week = request.form.get('classes_per_week', 1, type=int)
        attended_classes = request.form.get('attended_classes', 0, type=int)
        
        # Validation
        if not subject_name:
            flash('Please enter the subject name.', 'error')
            return render_template('attendance.html', 
                                 attendances=attendances,
                                 subjects=subjects)
        
        if total_weeks < 1 or total_weeks > 20:
            flash('Total weeks must be between 1 and 20.', 'error')
            return render_template('attendance.html',
                                 attendances=attendances,
                                 subjects=subjects)
        
        if classes_per_week < 1 or classes_per_week > 5:
            flash('Classes per week must be between 1 and 5.', 'error')
            return render_template('attendance.html',
                                 attendances=attendances,
                                 subjects=subjects)
        
        total_classes = total_weeks * classes_per_week
        
        if attended_classes < 0 or attended_classes > total_classes:
            flash(f'Attended classes must be between 0 and {total_classes}.', 'error')
            return render_template('attendance.html',
                                 attendances=attendances,
                                 subjects=subjects)
        
        # Check if attendance record exists
        existing = Attendance.query.filter_by(
            user_id=current_user.id,
            subject_name=subject_name
        ).first()
        
        if existing:
            # Update existing record
            existing.total_weeks = total_weeks
            existing.classes_per_week = classes_per_week
            existing.attended_classes = attended_classes
            attendance = existing
            flash(f'Attendance for {subject_name} updated!', 'success')
        else:
            # Create new record
            attendance = Attendance(
                user_id=current_user.id,
                subject_name=subject_name,
                total_weeks=total_weeks,
                classes_per_week=classes_per_week,
                attended_classes=attended_classes
            )
            db.session.add(attendance)
            flash(f'Attendance for {subject_name} saved!', 'success')
        
        try:
            db.session.commit()
            
            # Prepare result for display
            result = {
                'subject': subject_name,
                'total_classes': attendance.total_classes,
                'attended': attended_classes,
                'percentage': attendance.attendance_percentage,
                'is_barred': attendance.is_barred,
                'classes_needed': attendance.classes_needed,
                'remaining_classes': attendance.total_classes - attended_classes
            }
            
            # Refresh attendance list
            attendances = Attendance.query.filter_by(user_id=current_user.id)\
                .order_by(Attendance.updated_at.desc()).all()
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            print(f"Attendance error: {e}")
    
    return render_template('attendance.html',
                         attendances=attendances,
                         subjects=subjects,
                         result=result)


@attendance_bp.route('/attendance/calculate', methods=['POST'])
@login_required
def calculate():
    """
    AJAX endpoint for quick attendance calculation.
    Does not save to database.
    """
    data = request.get_json()
    
    total_weeks = data.get('total_weeks', 14)
    classes_per_week = data.get('classes_per_week', 1)
    attended_classes = data.get('attended_classes', 0)
    
    total_classes = total_weeks * classes_per_week
    
    if total_classes == 0:
        return jsonify({'error': 'Invalid input'}), 400
    
    percentage = (attended_classes / total_classes) * 100
    is_barred = percentage < 80
    
    # Calculate classes needed to reach 80%
    classes_needed = 0
    if is_barred:
        required = total_classes * 0.80
        classes_needed = max(0, int(required - attended_classes + 1))
    
    return jsonify({
        'total_classes': total_classes,
        'attended': attended_classes,
        'percentage': round(percentage, 2),
        'is_barred': is_barred,
        'classes_needed': classes_needed,
        'remaining_classes': total_classes - attended_classes
    })


@attendance_bp.route('/attendance/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete an attendance record"""
    attendance = Attendance.query.get_or_404(id)
    
    # Verify ownership
    if attendance.user_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('attendance.index'))
    
    subject_name = attendance.subject_name
    
    try:
        db.session.delete(attendance)
        db.session.commit()
        flash(f'Attendance record for {subject_name} deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
        print(f"Delete error: {e}")
    
    return redirect(url_for('attendance.index'))
