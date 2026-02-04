"""
Timetable Routes - Class schedule management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, time
from app import db
from models.database import Timetable

timetable_bp = Blueprint('timetable', __name__, url_prefix='/timetable')

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
COLORS = [
    '#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
    '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
]


@timetable_bp.route('/')
@login_required
def index():
    """View weekly timetable"""
    classes = current_user.timetables.order_by(Timetable.day, Timetable.start_time).all()
    
    # Organize by day
    schedule = {day: [] for day in DAYS}
    for cls in classes:
        if cls.day in schedule:
            schedule[cls.day].append(cls)
    
    return render_template('timetable.html',
                         schedule=schedule,
                         days=DAYS,
                         colors=COLORS)


@timetable_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_class():
    """Add a new class to timetable"""
    if request.method == 'POST':
        try:
            start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
            end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
            
            new_class = Timetable(
                user_id=current_user.id,
                subject_code=request.form.get('subject_code', '').strip().upper(),
                subject_name=request.form['subject_name'].strip(),
                day=request.form['day'],
                start_time=start_time,
                end_time=end_time,
                venue=request.form.get('venue', '').strip(),
                lecturer=request.form.get('lecturer', '').strip(),
                section=request.form.get('section', '').strip(),
                color=request.form.get('color', '#4F46E5')
            )
            
            db.session.add(new_class)
            db.session.commit()
            
            flash(f'Class "{new_class.subject_name}" added! 📚', 'success')
            return redirect(url_for('timetable.index'))
            
        except Exception as e:
            flash(f'Error adding class: {str(e)}', 'error')
    
    return render_template('timetable_form.html',
                         days=DAYS,
                         colors=COLORS,
                         class_item=None)


@timetable_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_class(id):
    """Edit existing class"""
    class_item = Timetable.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            class_item.subject_code = request.form.get('subject_code', '').strip().upper()
            class_item.subject_name = request.form['subject_name'].strip()
            class_item.day = request.form['day']
            class_item.start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
            class_item.end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
            class_item.venue = request.form.get('venue', '').strip()
            class_item.lecturer = request.form.get('lecturer', '').strip()
            class_item.section = request.form.get('section', '').strip()
            class_item.color = request.form.get('color', '#4F46E5')
            
            db.session.commit()
            flash('Class updated! ✅', 'success')
            return redirect(url_for('timetable.index'))
            
        except Exception as e:
            flash(f'Error updating class: {str(e)}', 'error')
    
    return render_template('timetable_form.html',
                         days=DAYS,
                         colors=COLORS,
                         class_item=class_item)


@timetable_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_class(id):
    """Delete a class"""
    class_item = Timetable.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(class_item)
        db.session.commit()
        flash('Class removed from timetable 🗑️', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error removing class. Please try again.', 'error')
        print(f"Delete class error: {e}")
        
    return redirect(url_for('timetable.index'))


@timetable_bp.route('/today')
@login_required
def today():
    """Get today's classes"""
    today_name = datetime.now().strftime('%A')
    classes = current_user.timetables.filter_by(day=today_name).order_by(Timetable.start_time).all()
    return render_template('timetable_today.html', classes=classes, day=today_name)


@timetable_bp.route('/api/classes')
@login_required
def api_classes():
    """API endpoint for getting classes (for calendar integration)"""
    classes = current_user.timetables.all()
    return jsonify([{
        'id': c.id,
        'subject': c.subject_name,
        'code': c.subject_code,
        'day': c.day,
        'start': c.start_time.strftime('%H:%M'),
        'end': c.end_time.strftime('%H:%M'),
        'venue': c.venue,
        'color': c.color
    } for c in classes])
