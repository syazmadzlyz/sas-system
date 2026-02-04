"""
Dashboard Routes for Student Assistant System
Main user interface after login - Enhanced with new features
"""
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.database import (
    Subject, Attendance, Result, CGPAHistory, calculate_cgpa,
    Timetable, ExamSchedule, Assignment
)
from models.ml_model import StudentRiskPredictor

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)

# Initialize risk predictor - MOVED TO APP CONTEXT
# predictor = StudentRiskPredictor()


@dashboard_bp.route('/dashboard')
@login_required
def index():
    """
    Main dashboard page.
    """
    # Get user data
    from flask import current_app
    predictor = current_app.predictor
    """
    Main dashboard page.
    
    Displays:
    - User welcome message
    - Current CGPA
    - Today's classes
    - Upcoming assignments and exams
    - Risk assessment
    - Quick actions
    """
    # Get user data
    user = current_user
    today = date.today()
    today_name = today.strftime('%A')
    
    # Get subjects
    subjects = Subject.query.filter_by(user_id=user.id).all()
    
    # Get attendance records
    attendances = Attendance.query.filter_by(user_id=user.id).all()
    
    # Get results
    results = Result.query.filter_by(user_id=user.id).all()
    
    # Get CGPA history
    cgpa_history = CGPAHistory.query.filter_by(user_id=user.id)\
        .order_by(CGPAHistory.timestamp.desc()).all()
    
    # Calculate current CGPA
    current_cgpa = user.get_current_cgpa()
    if current_cgpa == 0 and subjects:
        current_cgpa = calculate_cgpa(subjects)
    
    # Calculate statistics
    total_credits = sum(s.credit_hours for s in subjects) if subjects else 0
    total_subjects = len(subjects)
    
    # Calculate average attendance
    avg_attendance = 100.0
    if attendances:
        avg_attendance = sum(a.attendance_percentage for a in attendances) / len(attendances)
    
    # Calculate average carry marks
    avg_carry = 70.0
    if results:
        avg_carry = sum(r.carry_percentage for r in results) / len(results)
    
    # Predict risk level
    risk_level = predictor.predict_risk(avg_attendance, avg_carry, current_cgpa)
    risk_proba = predictor.predict_risk_proba(avg_attendance, avg_carry, current_cgpa)
    
    # Find at-risk subjects (attendance < 80%)
    at_risk_subjects = [a for a in attendances if a.is_barred]
    
    # Find weak subjects (carry mark < 50%)
    weak_subjects = [r for r in results if r.carry_percentage < 50]
    
    # Get today's classes from timetable
    today_classes = Timetable.query.filter_by(
        user_id=user.id,
        day=today_name
    ).order_by(Timetable.start_time).all()
    
    # Get upcoming exams (next 30 days)
    upcoming_exams = ExamSchedule.query.filter(
        ExamSchedule.user_id == user.id,
        ExamSchedule.exam_date >= today
    ).order_by(ExamSchedule.exam_date).limit(5).all()
    
    # Get upcoming assignments (pending, next 14 days)
    upcoming_assignments = Assignment.query.filter(
        Assignment.user_id == user.id,
        Assignment.status.in_(['pending', 'in_progress']),
        Assignment.deadline >= datetime.now()
    ).order_by(Assignment.deadline).limit(5).all()
    
    # Prepare chart data for CGPA history
    chart_labels = [h.semester for h in reversed(cgpa_history[-6:])]  # Last 6 semesters
    chart_data = [h.cgpa for h in reversed(cgpa_history[-6:])]
    
    return render_template('dashboard.html',
        user=user,
        subjects=subjects,
        attendances=attendances,
        results=results,
        cgpa_history=cgpa_history,
        current_cgpa=current_cgpa,
        total_credits=total_credits,
        total_subjects=total_subjects,
        avg_attendance=avg_attendance,
        avg_carry=avg_carry,
        risk_level=risk_level,
        risk_proba=risk_proba,
        at_risk_subjects=at_risk_subjects,
        weak_subjects=weak_subjects,
        chart_labels=chart_labels,
        chart_data=chart_data,
        today_classes=today_classes,
        upcoming_exams=upcoming_exams,
        upcoming_assignments=upcoming_assignments
    )
