"""
AI Study Assistant Routes for Student Assistant System
Provides intelligent study recommendations using ML
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.database import Subject, Attendance, Result, CGPAHistory, calculate_cgpa
from models.ml_model import StudentRiskPredictor, StudyAssistant

# Create blueprint
assistant_bp = Blueprint('assistant', __name__)

# Initialize ML components - MOVED TO APP CONTEXT
# predictor = StudentRiskPredictor()
# study_assistant = StudyAssistant()


@assistant_bp.route('/assistant')
@login_required
def index():
    """
    AI Study Assistant page.
    """
    # Get ML components from app context
    from flask import current_app
    predictor = current_app.predictor
    study_assistant = current_app.study_assistant

    # Get user data
    user = current_user
    
    # Get attendance records
    attendances = Attendance.query.filter_by(user_id=user.id).all()
    
    # Get results
    results = Result.query.filter_by(user_id=user.id).all()
    
    # Get subjects
    subjects = Subject.query.filter_by(user_id=user.id).all()
    
    # Get current CGPA
    cgpa = user.get_current_cgpa()
    if cgpa == 0 and subjects:
        cgpa = calculate_cgpa(subjects)
    
    # Perform comprehensive analysis
    analysis = study_assistant.analyze_student(attendances, results, cgpa)
    
    # Get feature importance for explanation
    feature_importance = predictor.get_feature_importance()
    
    # Prepare data for charts
    attendance_data = []
    for a in attendances:
        attendance_data.append({
            'subject': a.subject_name,
            'percentage': a.attendance_percentage,
            'is_barred': a.is_barred
        })
    
    result_data = []
    for r in results:
        result_data.append({
            'subject': r.subject_name,
            'carry_percentage': r.carry_percentage,
            'passed_carry': r.passed_carry
        })
    
    return render_template('assistant.html',
                         user=user,
                         analysis=analysis,
                         attendances=attendance_data,
                         results=result_data,
                         cgpa=cgpa,
                         feature_importance=feature_importance)


@assistant_bp.route('/assistant/ask', methods=['POST'])
@login_required
def ask():
    """
    AJAX endpoint for quick advice.
    """
    from flask import current_app
    study_assistant = current_app.study_assistant
    
    data = request.get_json()
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'Please enter a question'}), 400
    
    # Get quick advice
    response = study_assistant.get_quick_advice(question)
    
    return jsonify({
        'question': question,
        'answer': response
    })


@assistant_bp.route('/assistant/predict', methods=['POST'])
@login_required
def predict():
    """
    AJAX endpoint for risk prediction.
    """
    from flask import current_app
    predictor = current_app.predictor
    data = request.get_json()
    attendance = float(data.get('attendance', 0))
    carry_mark = float(data.get('carry_mark', 0))
    past_gpa = float(data.get('past_gpa', 0))
    
    # Calculate risk
    risk = predictor.predict_risk(attendance, carry_mark, past_gpa)
    probabilities = predictor.predict_risk_proba(attendance, carry_mark, past_gpa)
    
    # Get recommendations
    recommendations = predictor.get_study_recommendation(risk)
    
    return jsonify({
        'risk_level': risk,
        'probabilities': {k: round(v * 100, 1) for k, v in probabilities.items()},
        'study_hours': recommendations['study_hours'],
        'priority': recommendations['priority'],
        'advice': recommendations['advice'][:3]  # Return top 3 advice
    })


@assistant_bp.route('/assistant/resources')
@login_required
def resources():
    """
    Get study resources based on user's current risk level.
    """
    from flask import current_app
    study_assistant = current_app.study_assistant
    
    # Get user data for analysis
    user = current_user
    attendances = Attendance.query.filter_by(user_id=user.id).all()
    results = Result.query.filter_by(user_id=user.id).all()
    subjects = Subject.query.filter_by(user_id=user.id).all()
    cgpa = user.get_current_cgpa() or calculate_cgpa(subjects)
    
    # Get analysis
    analysis = study_assistant.analyze_student(attendances, results, cgpa)
    recommendations = analysis.get('recommendations', {})
    resources = recommendations.get('resources', [])
    
    # Add additional resources
    all_resources = resources + [
        {'name': 'NotebookLM', 'url': 'https://notebooklm.google.com/', 'desc': 'Google AI-powered study assistant'},
        {'name': 'Wolfram Alpha', 'url': 'https://www.wolframalpha.com/', 'desc': 'Computational knowledge engine'},
        {'name': 'Symbolab', 'url': 'https://www.symbolab.com/', 'desc': 'Math solver with steps'},
        {'name': 'Grammarly', 'url': 'https://www.grammarly.com/', 'desc': 'Writing assistant'},
        {'name': 'Zotero', 'url': 'https://www.zotero.org/', 'desc': 'Reference management'},
    ]
    
    return jsonify({
        'risk_level': analysis['risk_level'],
        'resources': all_resources
    })
