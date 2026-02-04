"""
Database Models for Student Assistant System
Enhanced for IIUM Students with comprehensive academic tracking
Uses SQLAlchemy ORM for data persistence
"""
from datetime import datetime, date, time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db


# ============================================
# IIUM Kulliyyah List
# ============================================
KULLIYYAH_CHOICES = [
    ('KICT', 'Kulliyyah of Information & Communication Technology'),
    ('KENMS', 'Kulliyyah of Economics & Management Sciences'),
    ('KAED', 'Kulliyyah of Architecture & Environmental Design'),
    ('KOE', 'Kulliyyah of Engineering'),
    ('KIRKHS', 'Kulliyyah of Islamic Revealed Knowledge & Human Sciences'),
    ('KOL', 'Ahmad Ibrahim Kulliyyah of Laws'),
    ('KOM', 'Kulliyyah of Medicine'),
    ('KOD', 'Kulliyyah of Dentistry'),
    ('KOP', 'Kulliyyah of Pharmacy'),
    ('KAHS', 'Kulliyyah of Allied Health Sciences'),
    ('KON', 'Kulliyyah of Nursing'),
    ('KOS', 'Kulliyyah of Science'),
    ('CELPAD', 'Centre for Languages and Pre-University Academic Development'),
    ('CFL', 'Centre for Foundation Studies'),
]

PROGRAM_LEVELS = [
    ('foundation', 'Foundation'),
    ('diploma', 'Diploma'),
    ('undergraduate', 'Undergraduate (Bachelor)'),
    ('postgraduate_masters', 'Postgraduate (Masters)'),
    ('postgraduate_phd', 'Postgraduate (PhD)'),
]


class User(UserMixin, db.Model):
    """User model for authentication and profile management."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Admin & Analytics Fields
    is_admin = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    warning_count = db.Column(db.Integer, default=0)
    
    # Password Reset Fields
    reset_requested = db.Column(db.Boolean, default=False)
    reset_approved = db.Column(db.Boolean, default=False)
    
    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')
    subjects = db.relationship('Subject', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    attendances = db.relationship('Attendance', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    results = db.relationship('Result', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    cgpa_history = db.relationship('CGPAHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    timetables = db.relationship('Timetable', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    exam_schedules = db.relationship('ExamSchedule', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    finances = db.relationship('Finance', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_current_cgpa(self):
        latest = self.cgpa_history.order_by(CGPAHistory.timestamp.desc()).first()
        return latest.cgpa if latest else 0.0
    
    def get_total_credits(self):
        return sum(s.credit_hours for s in self.subjects.all())
    
    def has_profile(self):
        return self.profile is not None
    
    def __repr__(self):
        return f'<User {self.username}>'


class Profile(db.Model):
    """Extended profile for IIUM students."""
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    matric_number = db.Column(db.String(20), nullable=True)
    kulliyyah = db.Column(db.String(20), nullable=True)
    program_name = db.Column(db.String(100), nullable=True)
    program_level = db.Column(db.String(30), nullable=True)
    current_semester = db.Column(db.Integer, default=1)
    intake_year = db.Column(db.Integer, nullable=True)
    expected_graduation = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_kulliyyah_name(self):
        for code, name in KULLIYYAH_CHOICES:
            if code == self.kulliyyah:
                return name
        return self.kulliyyah
    
    def get_level_name(self):
        for code, name in PROGRAM_LEVELS:
            if code == self.program_level:
                return name
        return self.program_level
    
    def __repr__(self):
        return f'<Profile {self.matric_number}>'


class Subject(db.Model):
    """Subject model for storing course information."""
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=True)
    credit_hours = db.Column(db.Integer, nullable=False, default=3)
    grade = db.Column(db.String(2), nullable=True)
    marks = db.Column(db.Float, nullable=True)
    grade_point = db.Column(db.Float, nullable=True)
    semester = db.Column(db.String(20), nullable=True)
    # IIUM specific - variable weightage
    carry_weight = db.Column(db.Float, default=40)  # Carry mark percentage (40%, 50%, 60%, 70%)
    final_weight = db.Column(db.Float, default=60)  # Final exam percentage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    attendance = db.relationship('Attendance', backref='subject', uselist=False, cascade='all, delete-orphan')
    result = db.relationship('Result', backref='subject', uselist=False, cascade='all, delete-orphan')
    
    def calculate_grade(self):
        """Calculate grade based on marks using IIUM grading scheme"""
        if self.marks is None:
            return None
        
        marks = self.marks
        if marks >= 80:
            self.grade, self.grade_point = 'A', 4.00
        elif marks >= 75:
            self.grade, self.grade_point = 'A-', 3.67
        elif marks >= 70:
            self.grade, self.grade_point = 'B+', 3.33
        elif marks >= 65:
            self.grade, self.grade_point = 'B', 3.00
        elif marks >= 60:
            self.grade, self.grade_point = 'B-', 2.67
        elif marks >= 55:
            self.grade, self.grade_point = 'C+', 2.33
        elif marks >= 50:
            self.grade, self.grade_point = 'C', 2.00
        elif marks >= 45:
            self.grade, self.grade_point = 'D', 1.67
        elif marks >= 40:
            self.grade, self.grade_point = 'D-', 1.33
        elif marks >= 35:
            self.grade, self.grade_point = 'E', 1.00
        else:
            self.grade, self.grade_point = 'F', 0.00
        
        return self.grade
    
    def __repr__(self):
        return f'<Subject {self.name}>'


class Attendance(db.Model):
    """Attendance tracking with 80% bar prediction."""
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    subject_name = db.Column(db.String(100), nullable=False)
    total_weeks = db.Column(db.Integer, nullable=False, default=14)
    classes_per_week = db.Column(db.Integer, nullable=False, default=1)
    attended_classes = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def total_classes(self):
        return self.total_weeks * self.classes_per_week
    
    @property
    def attendance_percentage(self):
        total = self.total_classes
        if total == 0:
            return 0.0
        return (self.attended_classes / total) * 100
    
    @property
    def is_barred(self):
        return self.attendance_percentage < 80
    
    @property
    def classes_needed(self):
        if not self.is_barred:
            return 0
        total = self.total_classes
        required = total * 0.80
        return max(0, int(required - self.attended_classes + 1))
    
    def __repr__(self):
        return f'<Attendance {self.subject_name}: {self.attendance_percentage:.1f}%>'


class Result(db.Model):
    """
    Result model with IIUM-specific marking scheme.
    Supports variable carry/final weightage.
    Must achieve 35% in BOTH carry and final to pass.
    """
    __tablename__ = 'results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    subject_name = db.Column(db.String(100), nullable=False)
    # Carry mark section
    carry_mark = db.Column(db.Float, nullable=True)
    carry_max = db.Column(db.Float, default=40)  # Can be 40, 50, 60, 70
    # Final exam section
    final_mark = db.Column(db.Float, nullable=True)
    final_max = db.Column(db.Float, default=60)  # Remaining percentage
    total_marks = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # IIUM passing threshold is 35%
    PASSING_THRESHOLD = 0.35
    
    @property
    def carry_percentage(self):
        if self.carry_mark is None or self.carry_max == 0:
            return 0.0
        return (self.carry_mark / self.carry_max) * 100
    
    @property
    def final_percentage(self):
        if self.final_mark is None or self.final_max == 0:
            return 0.0
        return (self.final_mark / self.final_max) * 100
    
    @property
    def minimum_carry_to_pass(self):
        """35% of carry max (e.g., 35% of 70 = 24.5)"""
        return self.carry_max * self.PASSING_THRESHOLD
    
    @property
    def minimum_final_to_pass(self):
        """35% of final max (e.g., 35% of 55 = 19.25)"""
        return self.final_max * self.PASSING_THRESHOLD
    
    @property
    def passed_carry(self):
        """Must achieve 35% of carry mark to pass"""
        if self.carry_mark is None:
            return False
        return self.carry_mark >= self.minimum_carry_to_pass
    
    @property
    def passed_final(self):
        """Must achieve 35% of final to pass"""
        if self.final_mark is None:
            return False
        return self.final_mark >= self.minimum_final_to_pass
    
    @property
    def passed_overall(self):
        """Must pass BOTH carry and final"""
        return self.passed_carry and self.passed_final
    
    @property
    def carry_marks_needed(self):
        """How many more marks needed to pass carry"""
        if self.carry_mark is None:
            return self.minimum_carry_to_pass
        needed = self.minimum_carry_to_pass - self.carry_mark
        return max(0, needed)
    
    @property
    def final_marks_needed(self):
        """How many more marks needed to pass final"""
        if self.final_mark is None:
            return self.minimum_final_to_pass
        needed = self.minimum_final_to_pass - self.final_mark
        return max(0, needed)
    
    def calculate_total(self):
        carry = self.carry_mark or 0
        final = self.final_mark or 0
        self.total_marks = carry + final
        return self.total_marks
    
    def __repr__(self):
        return f'<Result {self.subject_name}: {self.total_marks}>'


class CGPAHistory(db.Model):
    """CGPA History for semester-wise tracking."""
    __tablename__ = 'cgpa_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    gpa = db.Column(db.Float, nullable=False, default=0.0)
    cgpa = db.Column(db.Float, nullable=False, default=0.0)
    total_credits = db.Column(db.Integer, default=0)
    total_subjects = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CGPAHistory {self.semester}: CGPA={self.cgpa:.2f}>'


class Timetable(db.Model):
    """Class timetable for weekly schedule."""
    __tablename__ = 'timetables'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_code = db.Column(db.String(20), nullable=True)
    subject_name = db.Column(db.String(100), nullable=False)
    day = db.Column(db.String(10), nullable=False)  # Monday, Tuesday, etc.
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    venue = db.Column(db.String(50), nullable=True)
    lecturer = db.Column(db.String(100), nullable=True)
    color = db.Column(db.String(7), default='#4F46E5')  # Hex color
    section = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    @property
    def duration_minutes(self):
        start = datetime.combine(date.today(), self.start_time)
        end = datetime.combine(date.today(), self.end_time)
        return int((end - start).total_seconds() / 60)
    
    def __repr__(self):
        return f'<Timetable {self.subject_name} - {self.day}>'


class ExamSchedule(db.Model):
    """Final exam schedule with countdown."""
    __tablename__ = 'exam_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_code = db.Column(db.String(20), nullable=True)
    subject_name = db.Column(db.String(100), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    duration_minutes = db.Column(db.Integer, default=180)  # 3 hours default
    venue = db.Column(db.String(100), nullable=True)
    seat_number = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def days_until(self):
        today = date.today()
        delta = self.exam_date - today
        return delta.days
    
    @property
    def is_upcoming(self):
        return self.days_until >= 0
    
    @property
    def is_soon(self):
        return 0 <= self.days_until <= 7
    
    def __repr__(self):
        return f'<ExamSchedule {self.subject_name} - {self.exam_date}>'


class Finance(db.Model):
    """Finance tracker for tuition and payments with partial/sponsored support."""
    __tablename__ = 'finances'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(20), nullable=False)  # fee, payment
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(db.String(20), nullable=True)  # full, partial, sponsored
    transaction_date = db.Column(db.Date, default=date.today)
    is_paid = db.Column(db.Boolean, default=False)
    receipt_number = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    CATEGORIES = [
        ('fee', 'Semester Fee'),
        ('payment', 'Payment Made'),
    ]
    
    PAYMENT_TYPES = [
        ('full', 'Full Payment'),
        ('partial', 'Partial Payment'),
        ('sponsored', 'Sponsored (PTPTN/JPA/etc)'),
    ]
    
    def __repr__(self):
        return f'<Finance {self.category}: RM{self.amount}>'


class Assignment(db.Model):
    """Assignment and deadline tracker."""
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_code = db.Column(db.String(20), nullable=True)
    subject_name = db.Column(db.String(100), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.DateTime, nullable=False)
    priority = db.Column(db.String(10), default='medium')  # low, medium, high, urgent
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, submitted, late
    weightage = db.Column(db.Float, nullable=True)  # Percentage of total marks
    submission_date = db.Column(db.DateTime, nullable=True)
    grade = db.Column(db.String(10), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    PRIORITIES = ['low', 'medium', 'high', 'urgent']
    STATUSES = ['pending', 'in_progress', 'submitted', 'late']
    
    @property
    def days_until_deadline(self):
        now = datetime.now()
        delta = self.deadline - now
        return delta.days
    
    @property
    def is_overdue(self):
        return datetime.now() > self.deadline and self.status not in ['submitted', 'late']
    
    @property
    def is_due_soon(self):
        return 0 <= self.days_until_deadline <= 3 and self.status == 'pending'
    
    def __repr__(self):
        return f'<Assignment {self.title}>'


class Task(db.Model):
    """Study planner and to-do tasks."""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    due_time = db.Column(db.Time, nullable=True)
    priority = db.Column(db.String(10), default='medium')
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    category = db.Column(db.String(30), nullable=True)  # study, assignment, revision, personal
    estimated_hours = db.Column(db.Float, nullable=True)
    actual_hours = db.Column(db.Float, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    CATEGORIES = ['study', 'assignment', 'revision', 'exam_prep', 'project', 'personal', 'other']
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    def complete(self):
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Task {self.title}>'


class Announcement(db.Model):
    """Global system announcements."""
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(20), default='info')  # info, warning, danger, success
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship only, no backref needed on User for simplicity unless required
    created_by = db.relationship('User', backref='announcements')
    
    def __repr__(self):
        return f'<Announcement {self.id}>'



# ============================================
# IIUM Grading Scheme - Utility functions
# ============================================
IIUM_GRADING_SCHEME = [
    (80, 100, 'A', 4.00),
    (75, 79, 'A-', 3.67),
    (70, 74, 'B+', 3.33),
    (65, 69, 'B', 3.00),
    (60, 64, 'B-', 2.67),
    (55, 59, 'C+', 2.33),
    (50, 54, 'C', 2.00),
    (45, 49, 'D', 1.67),
    (40, 44, 'D-', 1.33),
    (35, 39, 'E', 1.00),
    (0, 34, 'F', 0.00),
]


def get_grade_from_marks(marks):
    """Convert marks to grade and grade point using IIUM scheme"""
    for min_mark, max_mark, grade, point in IIUM_GRADING_SCHEME:
        if min_mark <= marks <= max_mark:
            return grade, point
    return 'F', 0.00


def get_grade_point_from_grade(grade):
    """Convert letter grade to grade point"""
    grade_map = {
        'A': 4.00, 'A-': 3.67,
        'B+': 3.33, 'B': 3.00, 'B-': 2.67,
        'C+': 2.33, 'C': 2.00,
        'D': 1.67, 'D-': 1.33,
        'E': 1.00, 'F': 0.00
    }
    return grade_map.get(grade.upper(), 0.00)


def calculate_gpa(subjects):
    """Calculate GPA from subjects."""
    if not subjects:
        return 0.0
    
    total_points = 0
    total_credits = 0
    
    for subject in subjects:
        if subject.grade_point is not None:
            total_points += subject.credit_hours * subject.grade_point
            total_credits += subject.credit_hours
    
    if total_credits == 0:
        return 0.0
    
    return total_points / total_credits


def calculate_cgpa(all_subjects):
    """Calculate CGPA from all subjects."""
    return calculate_gpa(all_subjects)
