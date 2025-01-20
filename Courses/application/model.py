from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func

db = SQLAlchemy()

class User(db.Model):
    # __tablename__ = 'Infosys_user'  # Table name

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)  # Password should be hashed
    role = db.Column(db.String(50), nullable=False, default='basic')
    isVerified = db.Column(db.String(20), nullable=False)
    answer = db.Column(db.String(50), nullable=False)

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
    created_at = db.Column(db.DateTime, default=func.now(), nullable=True)

    # Foreign key referencing User table
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
     # Enrollment Table
class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to Infosys_user
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)  # Link to courses
    status = db.Column(db.String(50), nullable=False, default="Not Enrolled")  # Enrolled, Completed
    enrolled_date = db.Column(db.DateTime, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)  # New column to track completion status
    
    # Audit Trail Table
class AuditTrail(db.Model):
    __tablename__ = 'audit_trail'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())


class Module(db.Model):
    __tablename__ = 'modules'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    objectives = db.Column(db.Text, nullable=True)
    learning_points = db.Column(db.Text, nullable=True)
    
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
    
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)  # Foreign key to Module
    created_at = db.Column(db.DateTime, default=func.now(), nullable=True)

    module = db.relationship('Module', backref='quizzes')
