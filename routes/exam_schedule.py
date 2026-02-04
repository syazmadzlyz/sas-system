"""
Exam Schedule Routes - Final exam schedule management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from models.database import ExamSchedule

exam_schedule_bp = Blueprint('exam_schedule', __name__, url_prefix='/exam-schedule')


@exam_schedule_bp.route('/')
@login_required
def index():
    """View exam schedule with countdown"""
    exams = current_user.exam_schedules.order_by(ExamSchedule.exam_date).all()
    
    # Separate upcoming and past exams
    today = date.today()
    upcoming = [e for e in exams if e.exam_date >= today]
    past = [e for e in exams if e.exam_date < today]
    
    return render_template('exam_schedule.html',
                         upcoming=upcoming,
                         past=past,
                         today=today)


@exam_schedule_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_exam():
    """Add a new exam to schedule"""
    if request.method == 'POST':
        try:
            exam_date = datetime.strptime(request.form['exam_date'], '%Y-%m-%d').date()
            start_time = None
            if request.form.get('start_time'):
                start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
            
            new_exam = ExamSchedule(
                user_id=current_user.id,
                subject_code=request.form.get('subject_code', '').strip().upper(),
                subject_name=request.form['subject_name'].strip(),
                exam_date=exam_date,
                start_time=start_time,
                duration_minutes=int(request.form.get('duration', 180)),
                venue=request.form.get('venue', '').strip(),
                seat_number=request.form.get('seat_number', '').strip(),
                notes=request.form.get('notes', '').strip()
            )
            
            db.session.add(new_exam)
            db.session.commit()
            
            flash(f'Exam "{new_exam.subject_name}" scheduled! 📝', 'success')
            return redirect(url_for('exam_schedule.index'))
            
        except Exception as e:
            flash(f'Error adding exam: {str(e)}', 'error')
    
    return render_template('exam_schedule_form.html', exam=None)


@exam_schedule_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_exam(id):
    """Edit existing exam"""
    exam = ExamSchedule.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            exam.subject_code = request.form.get('subject_code', '').strip().upper()
            exam.subject_name = request.form['subject_name'].strip()
            exam.exam_date = datetime.strptime(request.form['exam_date'], '%Y-%m-%d').date()
            if request.form.get('start_time'):
                exam.start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
            exam.duration_minutes = int(request.form.get('duration', 180))
            exam.venue = request.form.get('venue', '').strip()
            exam.seat_number = request.form.get('seat_number', '').strip()
            exam.notes = request.form.get('notes', '').strip()
            
            db.session.commit()
            flash('Exam updated! ✅', 'success')
            return redirect(url_for('exam_schedule.index'))
            
        except Exception as e:
            flash(f'Error updating exam: {str(e)}', 'error')
    
    return render_template('exam_schedule_form.html', exam=exam)


@exam_schedule_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_exam(id):
    """Delete an exam"""
    exam = ExamSchedule.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    db.session.delete(exam)
    db.session.commit()
    
    flash('Exam removed from schedule 🗑️', 'success')
    return redirect(url_for('exam_schedule.index'))


@exam_schedule_bp.route('/countdown')
@login_required
def countdown():
    """Get next exam countdown (for dashboard widget)"""
    next_exam = current_user.exam_schedules.filter(
        ExamSchedule.exam_date >= date.today()
    ).order_by(ExamSchedule.exam_date).first()
    
    if next_exam:
        return jsonify({
            'subject': next_exam.subject_name,
            'date': next_exam.exam_date.strftime('%Y-%m-%d'),
            'days_until': next_exam.days_until,
            'venue': next_exam.venue
        })
    return jsonify({'message': 'No upcoming exams'})
