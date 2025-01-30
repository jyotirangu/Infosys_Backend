from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func

db = SQLAlchemy()


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_id = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    instructor = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.String(50), nullable=False)
    end_date = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    
    # Adding column for discription of the course
    detailed_description = db.Column(db.String(500), nullable = True)
    
    # New column for storing creation date
    created_at = db.Column(db.String(50), nullable=True)
    created_by = db.Column(db.Integer, nullable=False)
    
     # Enrollment Table
class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)  # Link to Infosys_user
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)  # Link to courses
    status = db.Column(db.String(50), nullable=False, default="Not Enrolled")  # Enrolled, Completed
    enrolled_date = db.Column(db.DateTime, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)  # New column to track completion status
    
    # Audit Trail Table
class AuditTrail(db.Model):
    __tablename__ = 'audit_trail'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    user_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())



class Module(db.Model):
    __tablename__ = 'modules'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    objectives = db.Column(db.Text, nullable=True)
    learning_points = db.Column(db.Text, nullable=True)
    completion_percentage = db.Column(db.Float, nullable=True, default=0.0)  # Track module completion percentage
    
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)  # Foreign key to Course
    created_at = db.Column(db.DateTime, default=func.now(), nullable=True)

    course = db.relationship('Course', backref='modules')


class Quiz(db.Model):
    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question = db.Column(db.String(255), nullable=False)
    correct_answer = db.Column(db.String(255), nullable=False)
    marks = db.Column(db.Integer, nullable=True)
    options = db.Column(db.JSON, nullable=False)  # JSON column to store options as an array
    weightage = db.Column(db.Float, nullable=True, default=0.0)  # Weightage for calculating overall score
    
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)  # Foreign key to Module
    created_at = db.Column(db.DateTime, default=func.now(), nullable=True)

    module = db.relationship('Module', backref='quizzes')


class QuizResult(db.Model):
    __tablename__ = 'quiz_results'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)  # Foreign key to User
    module_id = db.Column(db.Integer, nullable=False)  # Foreign key to Quiz
    score = db.Column(db.Integer, nullable=True)  # Total score achieved by the user
    status = db.Column(db.String(50), nullable=True)  # e.g., Passed, Failed
    attempted_at = db.Column(db.DateTime, default=func.now(), nullable=True)  # Time when quiz was attempted
    total_marks = db.Column(db.Integer, nullable=False)  # Total possible marks of the quiz
    
    answers = db.Column(db.JSON, nullable=False)  # Store individual answers (e.g., {"Q1": "A", "Q2": "B"})
    correct_answers = db.Column(db.JSON, nullable=False)  # Correct answers (e.g., {"Q1": "A", "Q2": "C"})
    is_correct = db.Column(db.JSON, nullable=False)  # Whether answers are correct (e.g., {"Q1": True, "Q2": False})

    # New fields
    time_spent = db.Column(db.Integer, nullable=True)  # Time spent on quiz (in seconds)
    is_complete = db.Column(db.Boolean, default=False)  # Track whether the quiz is completed



class CourseProgress(db.Model):
    __tablename__ = 'course_progress'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)  # Foreign key to User
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)  # Foreign key to Course
    completion_percentage = db.Column(db.Float, default=0.0, nullable=False)  # Course completion percentage
    status = db.Column(db.String(50), nullable=False, default="In Progress")  # Active or Completed
    last_accessed = db.Column(db.DateTime, default=func.now(), nullable=True)  # Track when the course was last accessed

    course = db.relationship('Course', backref='course_progress')


class PerformanceAnalytics(db.Model):
    __tablename__ = 'performance_analytics'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)  # Foreign key to User
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)  # Foreign key to Course
    quizzes_taken = db.Column(db.Integer, default=0, nullable=True)  # Number of quizzes attempted
    modules_completed = db.Column(db.Integer, default=0, nullable=True)  # Number of modules completed
    total_score = db.Column(db.Integer, default=0, nullable=True)  # Total score from quizzes
    average_score = db.Column(db.Float, default=0.0, nullable=True)  # Average quiz score
    trends = db.Column(db.JSON, nullable=True)  # JSON data for trends (e.g., {"Week 1": 70, "Week 2": 80})

    course = db.relationship('Course', backref='performance_analytics')