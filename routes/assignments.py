"""
Assignment Routes - Assignment and deadline tracking
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app import db
from models.database import Assignment

assignments_bp = Blueprint('assignments', __name__, url_prefix='/assignments')


@assignments_bp.route('/')
@login_required
def index():
    """View all assignments"""
    assignments = current_user.assignments.order_by(Assignment.deadline).all()
    
    # Categorize assignments
    now = datetime.now()
    overdue = [a for a in assignments if a.deadline < now and a.status not in ['submitted', 'late']]
    due_soon = [a for a in assignments if 0 <= a.days_until_deadline <= 3 and a.status == 'pending']
    upcoming = [a for a in assignments if a.days_until_deadline > 3 and a.status in ['pending', 'in_progress']]
    completed = [a for a in assignments if a.status in ['submitted', 'late']]
    
    return render_template('assignments.html',
                         assignments=assignments,
                         overdue=overdue,
                         due_soon=due_soon,
                         upcoming=upcoming,
                         completed=completed)


@assignments_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_assignment():
    """Add a new assignment"""
    if request.method == 'POST':
        try:
            deadline_str = request.form['deadline']
            if 'T' in deadline_str:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
            else:
                deadline = datetime.strptime(deadline_str + ' 23:59', '%Y-%m-%d %H:%M')
            
            new_assignment = Assignment(
                user_id=current_user.id,
                subject_code=request.form.get('subject_code', '').strip().upper(),
                subject_name=request.form.get('subject_name', '').strip(),
                title=request.form['title'].strip(),
                description=request.form.get('description', '').strip(),
                deadline=deadline,
                priority=request.form.get('priority', 'medium'),
                weightage=float(request.form['weightage']) if request.form.get('weightage') else None,
                notes=request.form.get('notes', '').strip()
            )
            
            db.session.add(new_assignment)
            db.session.commit()
            
            flash(f'Assignment "{new_assignment.title}" added! 📝', 'success')
            return redirect(url_for('assignments.index'))
            
        except Exception as e:
            flash(f'Error adding assignment: {str(e)}', 'error')
    
    return render_template('assignment_form.html',
                         assignment=None,
                         priorities=Assignment.PRIORITIES)


@assignments_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_assignment(id):
    """Edit existing assignment"""
    assignment = Assignment.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            deadline_str = request.form['deadline']
            if 'T' in deadline_str:
                assignment.deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
            else:
                assignment.deadline = datetime.strptime(deadline_str + ' 23:59', '%Y-%m-%d %H:%M')
            
            assignment.subject_code = request.form.get('subject_code', '').strip().upper()
            assignment.subject_name = request.form.get('subject_name', '').strip()
            assignment.title = request.form['title'].strip()
            assignment.description = request.form.get('description', '').strip()
            assignment.priority = request.form.get('priority', 'medium')
            assignment.status = request.form.get('status', 'pending')
            assignment.weightage = float(request.form['weightage']) if request.form.get('weightage') else None
            assignment.grade = request.form.get('grade', '').strip()
            assignment.notes = request.form.get('notes', '').strip()
            
            if assignment.status == 'submitted' and not assignment.submission_date:
                assignment.submission_date = datetime.now()
            
            db.session.commit()
            flash('Assignment updated! ✅', 'success')
            return redirect(url_for('assignments.index'))
            
        except Exception as e:
            flash(f'Error updating assignment: {str(e)}', 'error')
    
    return render_template('assignment_form.html',
                         assignment=assignment,
                         priorities=Assignment.PRIORITIES,
                         statuses=Assignment.STATUSES)


@assignments_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_assignment(id):
    """Delete an assignment"""
    assignment = Assignment.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    db.session.delete(assignment)
    db.session.commit()
    
    flash('Assignment deleted 🗑️', 'success')
    return redirect(url_for('assignments.index'))


@assignments_bp.route('/submit/<int:id>', methods=['POST'])
@login_required
def submit_assignment(id):
    """Mark assignment as submitted"""
    assignment = Assignment.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if assignment.is_overdue:
        assignment.status = 'late'
    else:
        assignment.status = 'submitted'
    assignment.submission_date = datetime.now()
    
    db.session.commit()
    flash(f'Assignment "{assignment.title}" marked as submitted! ✅', 'success')
    return redirect(url_for('assignments.index'))


@assignments_bp.route('/calendar')
@login_required
def calendar():
    """Calendar view of assignments"""
    assignments = current_user.assignments.filter(
        Assignment.deadline >= date.today()
    ).order_by(Assignment.deadline).all()
    
    return render_template('assignments_calendar.html', assignments=assignments)


@assignments_bp.route('/api/upcoming')
@login_required
def api_upcoming():
    """Get upcoming assignments for dashboard widget"""
    upcoming = current_user.assignments.filter(
        Assignment.deadline >= datetime.now(),
        Assignment.status.in_(['pending', 'in_progress'])
    ).order_by(Assignment.deadline).limit(5).all()
    
    return jsonify([{
        'id': a.id,
        'title': a.title,
        'subject': a.subject_name,
        'deadline': a.deadline.isoformat(),
        'days_until': a.days_until_deadline,
        'priority': a.priority,
        'is_due_soon': a.is_due_soon
    } for a in upcoming])
