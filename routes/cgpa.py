"""
CGPA Calculator Routes for Student Assistant System
Handles GPA/CGPA calculation using IIUM grading scheme
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.database import (
    Subject, CGPAHistory, 
    get_grade_from_marks, get_grade_point_from_grade,
    calculate_gpa, calculate_cgpa
)
from app import db
from datetime import datetime

# Create blueprint
cgpa_bp = Blueprint('cgpa', __name__)


# IIUM Grading Scheme for display
IIUM_GRADING = [
    {'range': '80 - 100', 'grade': 'A', 'point': 4.00},
    {'range': '75 - 79', 'grade': 'A-', 'point': 3.67},
    {'range': '70 - 74', 'grade': 'B+', 'point': 3.33},
    {'range': '65 - 69', 'grade': 'B', 'point': 3.00},
    {'range': '60 - 64', 'grade': 'B-', 'point': 2.67},
    {'range': '55 - 59', 'grade': 'C+', 'point': 2.33},
    {'range': '50 - 54', 'grade': 'C', 'point': 2.00},
    {'range': '45 - 49', 'grade': 'D', 'point': 1.67},
    {'range': '40 - 44', 'grade': 'D-', 'point': 1.33},
    {'range': '35 - 39', 'grade': 'E', 'point': 1.00},
    {'range': '0 - 34', 'grade': 'F', 'point': 0.00},
]


@cgpa_bp.route('/cgpa', methods=['GET', 'POST'])
@login_required
def index():
    """
    CGPA calculator page.
    
    GET: Display calculator with existing subjects grouped by semester
    POST: Add new subject and recalculate
    """
    # Get existing subjects
    subjects = Subject.query.filter_by(user_id=current_user.id)\
        .order_by(Subject.semester.desc(), Subject.created_at.desc()).all()
    
    # Group subjects by semester
    semesters_dict = {}
    for s in subjects:
        sem = s.semester or "Uncategorized"
        if sem not in semesters_dict:
            semesters_dict[sem] = []
        semesters_dict[sem].append(s)
    
    # Calculate GPA for each semester
    semester_data = []
    for sem_name, sem_subjects in semesters_dict.items():
        sem_gpa = calculate_gpa(sem_subjects)
        sem_credits = sum(s.credit_hours for s in sem_subjects)
        semester_data.append({
            'name': sem_name,
            'subjects': sem_subjects,
            'gpa': sem_gpa,
            'credits': sem_credits,
            'count': len(sem_subjects)
        })
    
    # Get CGPA history
    history = CGPAHistory.query.filter_by(user_id=current_user.id)\
        .order_by(CGPAHistory.timestamp.desc()).all()
    
    # Calculate current GPA/CGPA (cumulative)
    current_gpa = calculate_gpa(subjects)
    current_cgpa = calculate_cgpa(subjects)
    total_credits = sum(s.credit_hours for s in subjects)
    
    if request.method == 'POST':
        action = request.form.get('action', 'add')
        
        if action == 'add':
            # Add new subject
            name = request.form.get('subject_name', '').strip()
            code = request.form.get('subject_code', '').strip()
            credit_hours = request.form.get('credit_hours', 3, type=int)
            input_type = request.form.get('input_type', 'marks')
            semester = request.form.get('semester', '').strip()
            
            # Validation
            if not name:
                flash('Please enter the subject name.', 'error')
                return render_template('cgpa.html',
                                     subjects=subjects,
                                     history=history,
                                     grading=IIUM_GRADING,
                                     current_gpa=current_gpa,
                                     current_cgpa=current_cgpa,
                                     total_credits=total_credits)
            
            if credit_hours < 1 or credit_hours > 6:
                flash('Credit hours must be between 1 and 6.', 'error')
                return render_template('cgpa.html',
                                     subjects=subjects,
                                     history=history,
                                     grading=IIUM_GRADING,
                                     current_gpa=current_gpa,
                                     current_cgpa=current_cgpa,
                                     total_credits=total_credits)
            
            # Create subject
            subject = Subject(
                user_id=current_user.id,
                name=name,
                code=code,
                credit_hours=credit_hours,
                semester=semester if semester else f"Sem {datetime.now().year}"
            )
            
            # Handle grade/marks input
            if input_type == 'marks':
                marks = request.form.get('marks', 0, type=float)
                if marks < 0 or marks > 100:
                    flash('Marks must be between 0 and 100.', 'error')
                    return render_template('cgpa.html',
                                         subjects=subjects,
                                         history=history,
                                         grading=IIUM_GRADING,
                                         current_gpa=current_gpa,
                                         current_cgpa=current_cgpa,
                                         total_credits=total_credits)
                
                subject.marks = marks
                grade, point = get_grade_from_marks(marks)
                subject.grade = grade
                subject.grade_point = point
            else:
                grade = request.form.get('grade', '').upper()
                if grade not in ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'D', 'D-', 'E', 'F']:
                    flash('Please select a valid grade.', 'error')
                    return render_template('cgpa.html',
                                         subjects=subjects,
                                         history=history,
                                         grading=IIUM_GRADING,
                                         current_gpa=current_gpa,
                                         current_cgpa=current_cgpa,
                                         total_credits=total_credits)
                
                subject.grade = grade
                subject.grade_point = get_grade_point_from_grade(grade)
            
            try:
                db.session.add(subject)
                db.session.commit()
                
                flash(f'Subject "{name}" added successfully!', 'success')
                return redirect(url_for('cgpa.index'))
                
            except Exception as e:
                db.session.rollback()
                flash('An error occurred. Please try again.', 'error')
                print(f"CGPA error: {e}")
        
        elif action == 'save_semester':
            # Save semester GPA/CGPA to history
            semester_name = request.form.get('semester_name', '').strip()
            
            if not semester_name:
                semester_name = f"Sem {len(history) + 1}"
            
            # Get subjects for this semester
            semester_subjects = [s for s in subjects if s.semester == semester_name]
            if not semester_subjects:
                semester_subjects = subjects  # Use all if no semester filter
            
            gpa = calculate_gpa(semester_subjects)
            cgpa = calculate_cgpa(subjects)  # CGPA is cumulative
            
            # Create history record
            record = CGPAHistory(
                user_id=current_user.id,
                semester=semester_name,
                gpa=gpa,
                cgpa=cgpa,
                total_credits=sum(s.credit_hours for s in semester_subjects),
                total_subjects=len(semester_subjects)
            )
            
            try:
                db.session.add(record)
                db.session.commit()
                flash(f'Semester "{semester_name}" saved to history!', 'success')
                
                # Refresh history
                history = CGPAHistory.query.filter_by(user_id=current_user.id)\
                    .order_by(CGPAHistory.timestamp.desc()).all()
                
            except Exception as e:
                db.session.rollback()
                flash('An error occurred. Please try again.', 'error')
                print(f"History error: {e}")
    
    return render_template('cgpa.html',
                         subjects=subjects,
                         semesters=semester_data,
                         history=history,
                         grading=IIUM_GRADING,
                         current_gpa=current_gpa,
                         current_cgpa=current_cgpa,
                         total_credits=total_credits)


@cgpa_bp.route('/cgpa/calculate', methods=['POST'])
@login_required
def calculate_ajax():
    """
    AJAX endpoint for quick GPA calculation.
    Does not save to database.
    """
    data = request.get_json()
    subjects = data.get('subjects', [])
    
    if not subjects:
        return jsonify({'error': 'No subjects provided'}), 400
    
    total_points = 0
    total_credits = 0
    
    results = []
    
    for s in subjects:
        name = s.get('name', 'Unknown')
        credit_hours = s.get('credit_hours', 3)
        marks = s.get('marks')
        grade = s.get('grade')
        
        if marks is not None:
            grade, point = get_grade_from_marks(float(marks))
        elif grade:
            point = get_grade_point_from_grade(grade)
        else:
            continue
        
        total_points += credit_hours * point
        total_credits += credit_hours
        
        results.append({
            'name': name,
            'credit_hours': credit_hours,
            'grade': grade,
            'grade_point': point,
            'quality_points': credit_hours * point
        })
    
    gpa = total_points / total_credits if total_credits > 0 else 0
    
    return jsonify({
        'gpa': round(gpa, 2),
        'total_credits': total_credits,
        'total_quality_points': round(total_points, 2),
        'subjects': results
    })


@cgpa_bp.route('/cgpa/delete/<int:id>', methods=['POST'])
@login_required
def delete_subject(id):
    """Delete a subject"""
    subject = Subject.query.get_or_404(id)
    
    # Verify ownership
    if subject.user_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('cgpa.index'))
    
    name = subject.name
    
    try:
        db.session.delete(subject)
        db.session.commit()
        flash(f'Subject "{name}" deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
        print(f"Delete error: {e}")
    
    return redirect(url_for('cgpa.index'))


@cgpa_bp.route('/cgpa/history/delete/<int:id>', methods=['POST'])
@login_required
def delete_history(id):
    """Delete a CGPA history record"""
    record = CGPAHistory.query.get_or_404(id)
    
    # Verify ownership
    if record.user_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('cgpa.index'))
    
    semester = record.semester
    
    try:
        db.session.delete(record)
        db.session.commit()
        flash(f'History for "{semester}" deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
        print(f"Delete error: {e}")
    
    return redirect(url_for('cgpa.index'))
