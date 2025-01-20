from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from .model import db
from .model import User, Course, Enrollment, AuditTrail, Module, Quiz
from .email import send_email
from datetime import datetime


# Create a Blueprint for course-related routes
AboutCourse = Blueprint('AboutCourse', __name__)


# Correct the log_audit_trail definition to accept data as an argument
def log_audit_trail(course, user, action):
    try:
        # course_id = data.get('course_id')
        # user_id = data.get('user_id')
        # action = data.get('action')

        # Create a new audit log
        new_audit = AuditTrail(
            course_id=course,
            user_id=user,
            action=action
        )
        db.session.add(new_audit)
        db.session.commit()
    except Exception as e:
        db.session.rollback()  # Rollback transaction in case of error
        print(f"Error logging audit trail: {str(e)}")
        
        
@AboutCourse.route('/courses/<int:user_id>', methods=['GET'])
def get_courses(user_id):
    try:
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found!"}), 404

        user_role = user.role
        # Fetch all courses ordered by the creation date
        courses = Course.query.order_by(Course.created_at.desc()).all()

        course_list = []
        for course in courses:
            # Check if the user is enrolled in the course
            enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=course.id).first()

            # Prepare the course data
            course_data = {
                "id": course.id,
                "course_id": course.course_id,
                "title": course.title,
                "description": course.description,
                "instructor": course.instructor,
                "start_date": course.start_date,
                "end_date": course.end_date,
                "duration": course.duration,
                "detailed_description": course.detailed_description,
                "created_at": course.created_at.strftime('%d-%m-%Y') if course.created_at else None,
                "created_by": {
                    "id": course.created_by,
                    "name": User.query.get(course.created_by).name,
                    "email": User.query.get(course.created_by).email
                },
                "modules": [],
                "is_enrolled": False,
                "enrollment_status": None
            }

            # Add modules and quizzes to the course data
            modules = Module.query.filter_by(course_id=course.id).all()
            for module in modules:
                module_data = {
                    "id": module.id,
                    "title": module.title,
                    "description": module.description,
                    "objectives": module.objectives,
                    "learning_points": module.learning_points,
                    "quizzes": [
                        {
                            "id": quiz.id,
                            "question": quiz.question,
                            "correct_answer": quiz.correct_answer,
                            "marks": quiz.marks,
                            "options": quiz.options
                        }
                        for quiz in module.quizzes
                    ]
                }
                course_data["modules"].append(module_data)

            # Check if the user is enrolled and set the enrollment status
            if enrollment:
                course_data["is_enrolled"] = True
                course_data["enrollment_status"] = enrollment.status

            # Add the course data to the course list
            course_list.append(course_data)

        # Apply conditional logic based on user role
        if user_role == 'Employee':
            # Only return basic course data for employees
            course_list = [
                {key: value for key, value in course.items() if key not in ['instructor', 'modules']}
                for course in course_list
            ]

        return jsonify({"courses": course_list}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@AboutCourse.route('/addCourse', methods=['POST'])
def add_course():
    try:
        # Parse incoming JSON data
        data = request.get_json()

        # Extract and validate primary course details
        course_id = data.get('course_id')
        title = data.get('title')
        description = data.get('description')
        instructor = data.get('instructor')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        duration = data.get('duration')
        created_by = data.get('created_by')
        detailed_description = data.get('detailed_description', '')

        if not all([course_id, title, description, instructor, start_date, end_date, duration, created_by]):
            return jsonify({"error": "All fields are required!"}), 400

        # Validate user existence
        user = User.query.get(created_by)
        if not user:
            return jsonify({"error": f"User with ID {created_by} not found!"}), 404

        # Create a new course
        new_course = Course(
            course_id=course_id,
            title=title,
            description=description,
            instructor=instructor,
            start_date=start_date,
            end_date=end_date,
            duration=duration,
            detailed_description=detailed_description,
            created_by=created_by
        )
        db.session.add(new_course)
        db.session.flush()  # Get the ID for related records

        # Add modules and quizzes
        modules = data.get('modules', [])
        for module_data in modules:
            new_module = Module(
                title=module_data.get('title'),
                description=module_data.get('description'),
                objectives=module_data.get('objectives'),
                learning_points=module_data.get('learningPoints'),
                course_id=new_course.id
            )
            db.session.add(new_module)
            db.session.flush()

            quizzes = module_data.get('quizzes', [])
            for quiz_data in quizzes:
                print("Quiz Data:", quiz_data)
                new_quiz = Quiz(
                    question=quiz_data.get('question'),
                    correct_answer=quiz_data.get('correctAnswer'),
                    marks=quiz_data.get('marks'),
                    options=quiz_data.get('options'),  # Add options field here
                    module_id=new_module.id
                )
                print(f"Adding Quiz: {new_quiz.question}, Module ID: {new_quiz.module_id}")
                db.session.add(new_quiz)
                
            # print(new_quiz)
            # db.session.add(new_quiz)

        # Commit the transaction
        db.session.commit()

        # Fetch all user emails for notifications
        users = User.query.all()
        recipient_emails = [user.email for user in users if user.email != "jyotirangu657@gmail.com"]

        # Send notifications
        for email in recipient_emails:
            send_email(
                sender_email="jyotirangu657@gmail.com",
                sender_password="avwt sldu agas ndpf",
                recipient_email=email,
                subject="New Course Added",
                body=f"A new course titled '{title}' has been added.\nStart Date: {start_date}\nDuration: {duration}",
                attachment_path=None
            )

        return jsonify({"message": "Course added successfully! Emails sent to users.", "course": {
            "id": new_course.id,
            "course_id": new_course.course_id,
            "title": new_course.title,
            "description": new_course.description,
            "instructor": new_course.instructor,
            "start_date": new_course.start_date,
            "end_date": new_course.end_date,
            "duration": new_course.duration,
            "created_at": new_course.created_at,
            "modules": [
                {
                    "id": module.id,
                    "title": module.title,
                    "description": module.description,
                    "objectives": module.objectives,
                    "learning_points": module.learning_points,
                    "quizzes": [
                        {
                            "id": quiz.id,
                            "question": quiz.question,
                            "correct_answer": quiz.correct_answer,
                            "marks": quiz.marks
                        }
                        for quiz in module.quizzes
                    ]
                }
                for module in new_course.modules
            ],
            "created_by": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }}), 201

    except Exception as e:
        db.session.rollback()  # Rollback in case of an error
        return jsonify({"error": str(e)}), 500




@AboutCourse.route('/instructor', methods=['GET'])
def get_instructors():
    try:
        # Query all users with the role of "instructor"
        instructors = User.query.filter_by(role='Instructor').all()

        # Format the data as JSON
        instructor_list = [
            {
                'id': instructor.id,
                'name': instructor.name,
                'email': instructor.email,
                'role': instructor.role,
                'isVerified': instructor.isVerified
            } for instructor in instructors
        ]

        return jsonify({
            'status': 'success',
            'instructors': instructor_list
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
        
 
 
# Create a new route in your backend for handling PUT requests to update a course.       
@AboutCourse.route("/editCourse/<int:course_id>", methods=["POST", "PUT"])
def edit_course(course_id):
    try:
        data = request.get_json()
        print(data)
        course = Course.query.get(course_id)
        user_id = data.get("userId")
        Dcourse= data.get("courseData")

        print("testing")
        print(Dcourse)
        print(user_id)

        if not course:
            return jsonify({"error": "Course not found!"}), 404

        course.title=Dcourse['title'] 
        course.description = Dcourse['description']
        course.start_date = Dcourse['start_date']
        course.end_date = Dcourse['end_date']
        course.duration = Dcourse['duration']
        # course.detailed_description = Dcourse['detailed_description']

        db.session.commit()
        
        # Log the action in the audit trail
        action = f"'{course.title}' is Edited."

        new_audit = AuditTrail(
            course_id=course_id,
            user_id=user_id,
            action=action
        )
        db.session.add(new_audit)
        db.session.commit()
        
        return jsonify({"message": "Course updated successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@AboutCourse.route('/course/enrolledcourses/<int:user_id>', methods=['GET'])
def get_enrolled_courses(user_id):
    try:
        # Get the user_id from query parameters or session
        # user_id = request.args.get('user_id')  # Adjust to retrieve from session if needed
        
        if not user_id:
            return jsonify({'error': 'User ID is required.'}), 400
        print(user_id)
        # Query for enrollments where the course is not yet completed
        enrollments = Enrollment.query.filter_by(user_id=user_id).all()
        print(enrollments)
        
        # If no enrollments found
        if not enrollments:
            return jsonify({'message': 'No enrolled courses found.'}), 404

        # Construct response data
        courses = []
        for enrollment in enrollments:
            course_details = Course.query.filter_by(id=enrollment.course_id).first()  # Assuming you have a Course table
            course = {
                'course_id': enrollment.course_id,
                'course_name': course_details.title,  # Include course title if available
                'status': enrollment.status,
                'enrolled_date': enrollment.enrolled_date.strftime('%Y-%m-%d %H:%M:%S') if enrollment.enrolled_date else None
            }
            courses.append(course)

        return jsonify({'enrolled_courses': courses}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@AboutCourse.route('/enroll', methods=['POST'])
def enroll_in_course():
    try:
        # Extract data from the request
        data = request.get_json()
        user_id = data.get('user_id')
        course_id = data.get('course_id')

        # Validate input
        if not user_id or not course_id:
            return jsonify({'error': 'User ID and Course ID are required.'}), 400

        # Check if the user is already enrolled
        existing_enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
        if existing_enrollment:
            return jsonify({'error': 'Already enrolled in this course.'}), 400

        # Create a new enrollment
        new_enrollment = Enrollment(
            user_id=user_id,
            course_id=course_id,
            status='Enrolled',
            enrolled_date=datetime.utcnow(),
            is_completed=False
        )

        # Add and commit the enrollment
        db.session.add(new_enrollment)
        db.session.commit()

        return jsonify({'message': 'Enrolled successfully!'}), 201

    except Exception as e:
        db.session.rollback()  # Rollback transaction in case of error
        return jsonify({'error': str(e)}), 500



@AboutCourse.route('/course/completed', methods=['POST'])
def complete_course():
    try:
        # Get the data from the request
        data = request.get_json()
        user_id = data.get('user_id')
        course_id = data.get('course_id')

        if not user_id or not course_id:
            return jsonify({'error': 'User ID and Course ID are required.'}), 400

        # Query for the enrollment record for the user and course
        enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()

        if not enrollment:
            return jsonify({'error': 'Enrollment not found.'}), 404

        # Update the enrollment record to mark it as completed
        enrollment.is_completed = True
        enrollment.status = 'Completed'
        db.session.commit()

        return jsonify({'message': 'Course marked as completed!'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



# Log an Action in the Audit Trail A route to log actions such as enrollment or course completion.

@AboutCourse.route('/course/audittrail', methods=['POST'])
def log_audit_trail():
    data = request.get_json()
    course_id = data.get('course_id')
    user_id = data.get('user_id')
    action = data.get('action')
    
    new_audit = AuditTrail(
        course_id=course_id,
        user_id=user_id,
        action=action
    )
    db.session.add(new_audit)
    db.session.commit()
    
    return jsonify({'message': 'Audit trail logged successfully!'}), 201



@AboutCourse.route('/course/audittrail', methods=['GET'])
def get_course_audit_trail():
    audit_trails = AuditTrail.query.all()
    
    actions = []
    for idx, audit in enumerate(audit_trails, start=1):  # Start the counter from 1
        user_name = User.query.filter_by(id=audit.user_id).first().name  # Fetch user name by user_id
        
        actions.append({
            'user_id': idx,  # Incremented counter
            'user_name': user_name,  # The user name fetched from the User model
            'action': audit.action,
            'timestamp': audit.timestamp
        })
    
    print(actions)
    return jsonify({'audit_trail': actions}), 200



# This route will accept a course_id and fetch the details from the User table along with the enrollment status.
@AboutCourse.route('/course/users/<int:course_id>', methods=['GET'])
def get_users_for_course(course_id):
    try:
        # Query the Enrollment table for users enrolled in the given course
        enrollments = Enrollment.query.filter_by(course_id=course_id).all()

        if not enrollments:
            return jsonify({"message": "No users found for this course."}), 404

        # Fetch user details along with their enrollment status
        users_list = [
            {
                "user_id": enrollment.user_id,
                "name": User.query.get(enrollment.user_id).name,
                "email": User.query.get(enrollment.user_id).email,
                "status": enrollment.status,  # Enrolled or Completed
                "enrolled_date": enrollment.enrolled_date,
                "is_completed": enrollment.is_completed
            }
            for enrollment in enrollments
        ]

        return jsonify({"course_id": course_id, "users": users_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@AboutCourse.route('/viewCourse/<int:user_id>/<int:course_id>', methods=['GET'])
def view_course(user_id, course_id):
    try:
        # Fetch the course details
        course = Course.query.get(course_id)
        if not course:
            return jsonify({"error": "Course not found!"}), 404

        # Fetch user details
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found!"}), 404

        # Fetch enrollment status for the current user
        enrollment = Enrollment.query.filter_by(course_id=course_id, user_id=user_id).first()
        enrollment_status = {
            "status": enrollment.status if enrollment else "Not Enrolled",
            "enrolled_date": enrollment.enrolled_date if enrollment else None,
            "is_completed": enrollment.is_completed if enrollment else False
        }

        # Fetch 'is_complete' filter from query parameters (optional)
        is_complete_filter = request.args.get('is_complete', None)

        # Fetch all employees and their enrollment statuses for this course
        employees = User.query.filter_by(role='Employee').all()  # Assuming 'Employee' role exists
        employee_enrollment_list = []
        for employee in employees:
            emp_enrollment = Enrollment.query.filter_by(course_id=course_id, user_id=employee.id).first()
            if emp_enrollment:
                emp_status = emp_enrollment.status
                emp_is_completed = emp_enrollment.is_completed
            else:
                emp_status = "Not Enrolled"
                emp_is_completed = False

            # Apply the completion filter if provided
            if is_complete_filter is not None:
                filter_value = is_complete_filter.lower() == 'true'
                if emp_is_completed != filter_value:
                    continue

            employee_enrollment_list.append({
                "user_id": employee.id,
                "name": employee.name,
                "email": employee.email,
                "status": emp_status,
                "enrolled_date": emp_enrollment.enrolled_date if emp_enrollment else None,
                "is_completed": emp_is_completed
            })

        # Prepare course details
        course_details = {
            "course_id": course.id,
            "title": course.title,
            "description": course.description,
            "instructor": course.instructor,
            "start_date": course.start_date,
            "end_date": course.end_date,
            "duration": course.duration,
            "created_by": {
                "id": course.created_by,
                "name": User.query.get(course.created_by).name,
                "email": User.query.get(course.created_by).email
            },
            "enrollment_status": enrollment_status,
            "user_details": {
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role
            },
            "employee_enrollments": employee_enrollment_list  # List of employees after applying the filter
        }

        return jsonify({"course_details": course_details}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
# Fetch All Unverified Users

@AboutCourse.route('/users/unverified', methods=['GET'])
def get_unverified_users():
    try:
        unverified_users = User.query.filter_by(isVerified="False").all()
        users = [
            {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
            for user in unverified_users
        ]
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
  
    
# Approve a User

@AboutCourse.route('/users/approve/<int:user_id>', methods=['PATCH'])
def approve_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.isVerified = "True"
        db.session.commit()
        return jsonify({"message": "User approved successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Disapprove or Reset a User

@AboutCourse.route('/users/disapprove/<int:user_id>', methods=['PATCH'])
def disapprove_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.isVerified = "False"
        db.session.commit()
        return jsonify({"message": "User disapproved successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500