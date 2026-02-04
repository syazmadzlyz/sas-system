"""
Main Flask Application Factory for Student Assistant System
Enhanced for IIUM Students with comprehensive features
"""
import os
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_name='development'):
    """
    Application factory function.
    Creates and configures the Flask application.
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Ensure instance folder exists for SQLite database
    instance_path = os.path.join(app.root_path, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Import and register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.attendance import attendance_bp
    from routes.cgpa import cgpa_bp
    from routes.exam import exam_bp
    from routes.assistant import assistant_bp
    from routes.profile import profile_bp
    from routes.timetable import timetable_bp
    from routes.exam_schedule import exam_schedule_bp
    from routes.finance import finance_bp
    from routes.assignments import assignments_bp
    from routes.planner import planner_bp
    from routes.admin import admin_bp
    
    # Register all blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(cgpa_bp)
    app.register_blueprint(exam_bp)
    app.register_blueprint(assistant_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(timetable_bp)
    app.register_blueprint(exam_schedule_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(assignments_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(admin_bp)
    
    # Create database tables
    with app.app_context():
        from models.database import (
            User, Profile, Subject, Attendance, Result, CGPAHistory,
            Timetable, ExamSchedule, Finance, Assignment, Task, Announcement
        )
        db.create_all()
        
        # Train ML model on startup (and attach to app context)
        from models.ml_model import StudentRiskPredictor, StudyAssistant
        
        # Instantiate and attach to app so blueprints can use them
        predictor = StudentRiskPredictor()
        predictor.train_model()
        app.predictor = predictor
        
        # Create study assistant with its own predictor (or we could share, but for now let's follow existing pattern)
        # Note: StudyAssistant creates a NEW predictor in its __init__. 
        # Ideally we should inject, but to avoid changing ml_model.py right now:
        study_assistant = StudyAssistant()
        app.study_assistant = study_assistant
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models.database import User
        return User.query.get(int(user_id))
    
    # Root route
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    # Context processor for templates
    @app.context_processor
    def inject_globals():
        """Inject global variables into all templates"""
        from datetime import date, datetime
        return {
            'current_date': date.today(),
            'current_date': date.today(),
            'current_datetime': datetime.now(),
            'active_announcement': Announcement.query.filter_by(is_active=True).first()
        }
        
    @app.before_request
    def update_last_seen():
        from flask_login import current_user
        from datetime import datetime
        if current_user.is_authenticated:
            current_user.last_seen = datetime.utcnow()
            try:
                db.session.commit()
            except:
                db.session.rollback()
    
    return app
