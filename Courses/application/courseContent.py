from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from .model import db
from .model import Course, Enrollment, AuditTrail, Module, Quiz, CourseProgress
from .email import send_email
from datetime import datetime
import requests

# Create a Blueprint for course-related routes
AboutCourse = Blueprint('AboutCourse', __name__)
# Base URL for the Authentication microservice
AUTH_SERVICE_URL = "http://localhost:5001"  

# Correct the log_audit_trail definition to accept data as an argument
def log_audit_trail(course, user, action):
    try:
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


def fetch_user_details(user_id):
    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/users/{user_id}")
        if response.status_code == 200:
            return response.json()  # Assuming the response is JSON formatted
        else:
            return None
    except requests.RequestException as e:
        print(f"Error fetching user details: {str(e)}")
        return None

@AboutCourse.route('/courses/<int:user_id>', methods=['GET'])
def get_courses(user_id):
    try:
        # Fetch user details from the authentication microservice
        user = fetch_user_details(user_id)
        print(user)
        if not user:
            return jsonify({"error": "User not found in the authentication service!"}), 404

        user_role = user.get("role")
        # Fetch all courses ordered by the creation date
        courses = Course.query.order_by(Course.created_at.desc()).all()
        

        course_list = []
        for course in courses:
            # Check if the user is enrolled in the course
            enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=course.id).first()
            courseprogress= CourseProgress.query.filter_by(user_id=user_id, course_id=course.id).first()
            # print(courseprogress.status)
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
                "status":courseprogress.status if courseprogress else None,
                 "enrollment_status": enrollment.status if enrollment else None,
                "detailed_description": course.detailed_description,
                "created_at": course.created_at,
                "created_by": course.created_by,  # Keep it as ID, since user data is fetched from another service
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

            # print(enrollment)
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
        

        # Fetch creator details from the authentication microservice
        creator = fetch_user_details(created_by)
        if not creator:
            return jsonify({"error": f"Creator with ID {created_by} not found in the authentication service!"}), 404
        
        created_at = datetime.now()

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
            created_by=created_by,
            created_at = datetime.now()
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
                new_quiz = Quiz(
                    question=quiz_data.get('question'),
                    correct_answer=quiz_data.get('correctAnswer'),
                    marks=quiz_data.get('marks'),
                    options=quiz_data.get('options'),
                    module_id=new_module.id
                )
                db.session.add(new_quiz)

        # Commit the transaction
        db.session.commit()

        # Fetch all user emails for notifications
        users = requests.get(f"{AUTH_SERVICE_URL}/users").json()  # Assuming it returns all users
        recipient_emails = [user['email'] for user in users if user['email'] != "jyotirangu657@gmail.com"]

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
            
        action = f"'{title}' is Added."

        new_audit = AuditTrail(
            course_id=course_id,
            user_id=users.user_id,
            action=action
        )
        db.session.add(new_audit)
        db.session.commit()

        return jsonify({"message": "Course added successfully! Emails sent to users."}), 201
    
    

    except Exception as e:
        db.session.rollback()  # Rollback in case of an error
        return jsonify({"error": str(e)}), 500


@AboutCourse.route('/instructor', methods=['GET'])
def get_instructors():
    try:
        # Make an API call to the Authentication microservice to get users with the role 'Instructor'
        response = requests.get(f'{AUTH_SERVICE_URL}/users')
        
        if response.status_code != 200:
            return jsonify({'status': 'error', 'message': 'Failed to fetch instructors!'}), response.status_code
        
        users = response.json()
        # Filter instructors from the API response
        instructors = [
            user for user in users if user['role'].lower() == 'instructor'
        ]

        return jsonify({
            'status': 'success',
            'instructors': instructors
        }), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@AboutCourse.route("/editCourse/<int:course_id>", methods=["POST", "PUT"])
def edit_course(course_id):
    try:
        data = request.get_json()
        Dcourse = data.get("courseData")
        user_id = data.get("userId")

        if not user_id:
            return jsonify({"error": "User ID is required!"}), 400

        # Fetch user details from Authentication microservice
        auth_service_url = f'http://localhost:5001/users/{user_id}'  # Replace with actual URL
        response = requests.get(auth_service_url)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch user details!"}), response.status_code
        
        user_details = response.json()

        # Fetch the course from the database
        course = Course.query.get(course_id)
        if not course:
            return jsonify({"error": "Course not found!"}), 404

        # Update course details
        course.title = Dcourse['title']
        course.description = Dcourse['description']
        course.start_date = Dcourse['start_date']
        course.end_date = Dcourse['end_date']
        course.duration = Dcourse['duration']
        course.detailed_description = Dcourse.get('detailed_description', course.detailed_description)
        course.created_by = user_id  # Assuming the user who edits is the creator

        db.session.commit()

        # Log the action in the audit trail
        action = f"'{course.title}' is Edited by {user_details['name']} ({user_details['email']})."
        new_audit = AuditTrail(course_id=course_id, user_id=user_id, action=action)
        db.session.add(new_audit)
        db.session.commit()

        return jsonify({"message": "Course updated successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@AboutCourse.route('/course/enrolledcourses/<int:user_id>', methods=['GET'])
def get_enrolled_courses(user_id):
    try:
        # Fetch user details from Authentication microservice
        auth_service_url = f'http://localhost:5001/users/{user_id}'  # Replace with actual URL
        user_response = requests.get(auth_service_url)
        if user_response.status_code != 200:
            return jsonify({'error': 'Failed to fetch user details!'}), user_response.status_code

        user_details = user_response.json()

        # Fetch enrollments for the user
        enrollments = Enrollment.query.filter_by(user_id=user_id).all()
        if not enrollments:
            return jsonify({'message': 'No enrolled courses found.'}), 404

        # Construct response data
        courses = []
        for enrollment in enrollments:
            course_details = Course.query.filter_by(id=enrollment.course_id).first()
            course = {
                'course_id': enrollment.course_id,
                'course_name': course_details.title if course_details else None,
                'status': enrollment.status,
                'enrolled_date': enrollment.enrolled_date.strftime('%Y-%m-%d %H:%M:%S') if enrollment.enrolled_date else None,
                'course_description': course_details.description if course_details else None,
                'detailed_description': course_details.detailed_description if course_details else None
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


# Mark Course as Completed

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

        # Log audit trail
        log_audit_trail_data = {
            'course_id': course_id,
            'user_id': user_id,
            'action': 'Course Completed'
        }
        log_audit_trail(log_audit_trail_data)

        return jsonify({'message': 'Course marked as completed!'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Log an Action in the Audit Trail

@AboutCourse.route('/course/audittrail', methods=['POST'])
def log_audit_trail(data):
    try:
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

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
@AboutCourse.route('/course/audittrail', methods=['GET'])
def get_audit_trail():
    try:
        audit_trails = AuditTrail.query.all()
        result = [
            {
                'id': audit.id,
                'course_id': audit.course_id,
                'user_id': audit.user_id,
                'action': audit.action,
                'timestamp': audit.timestamp 
            }
            for audit in audit_trails
        ]
        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@AboutCourse.route('/course/users/<int:course_id>', methods=['GET'])
def get_users_for_course(course_id):
    try:
        # Query the Enrollment table for users enrolled in the given course
        enrollments = Enrollment.query.filter_by(course_id=course_id).all()

        if not enrollments:
            return jsonify({"message": "No users found for this course."}), 404

        # Fetch user details along with their enrollment status
        users_list = []
        for enrollment in enrollments:
            # API call to Authentication microservice to fetch user details
            response = requests.get(f'http://localhost:5001/users/{enrollment.user_id}')
            if response.status_code == 200:
                user_data = response.json()
                users_list.append({
                    "user_id": enrollment.user_id,
                    "name": user_data['name'],
                    "email": user_data['email'],
                    "status": enrollment.status,  # Enrolled or Completed
                    "enrolled_date": enrollment.enrolled_date,
                    "is_completed": enrollment.is_completed
                })
            else:
                users_list.append({
                    "user_id": enrollment.user_id,
                    "name": 'Unknown',
                    "email": 'Unknown',
                    "status": enrollment.status,
                    "enrolled_date": enrollment.enrolled_date,
                    "is_completed": enrollment.is_completed
                })

        return jsonify({"course_id": course_id, "users": users_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@AboutCourse.route('/viewCourse/<int:user_id>/<int:course_id>', methods=['GET'])
def view_course(user_id, course_id):
    try:
        course = Course.query.get(course_id)
        if not course:
            return jsonify({"error": "Course not found!"}), 404

        # Fetch user details from the Authentication microservice
        auth_service_url = f"http://localhost:5001/users/{user_id}"
        auth_response = requests.get(auth_service_url)
        
        
        if auth_response.status_code != 200:
            return jsonify({"error": "Error fetching user data from authentication service"}), 500

        user = auth_response.json()
        # print(user)
        # Fetch user's enrollment status
        enrollment = Enrollment.query.filter_by(course_id=course_id, user_id=user_id).first()
        enrollment_status = {
            "status": enrollment.status if enrollment else "Not Enrolled",
            "is_completed": enrollment.is_completed if enrollment else False
        }
        
        print(course.created_at)
        return jsonify({
            "course_details": {
                "course_id": course.id,
                "title": course.title,
                "description": course.description,
                "instructor": course.instructor,
                "status": enrollment_status['status'],
                "is_completed": enrollment_status['is_completed'],
                "start_date": course.start_date,
                "end_date": course.end_date,
                "duration": course.duration,
                "created_at": course.created_at,
                "created_by": {
                    "id": course.created_by,
                    "name": user.get('name'),
                    "email": user.get('email')
                }
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Route to fetch all unverified users from Microservice 1
@AboutCourse.route('/users/unverified', methods=['GET'])
def get_unverified_users():
    try:
        # Make API call to Microservice 1 to get unverified users
        response = requests.get(f"http://localhost:5001/users/unverified")
        
        # If the response is successful
        if response.status_code == 200:
            unverified_users = response.json()
            return jsonify(unverified_users), 200
        else:
            return jsonify({"error": "Failed to fetch unverified users from Microservice 1"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
# Approve a User

@AboutCourse.route('/users/approve/<int:user_id>', methods=['PATCH'])
def approve_user(user_id):
    try:
        response = requests.patch(f"http://localhost:5001/users/approve/{user_id}")
        
        if response.status_code == 200:
            return jsonify({"message": "User approved successfully!"}), 200
        else:
            return jsonify({"error": "Failed to approve user in Microservice 1"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Disapprove or Reset a User

@AboutCourse.route('/users/disapprove/<int:user_id>', methods=['PATCH'])
def disapprove_user(user_id):
    try:
        response = requests.patch(f"http://localhost:5001/users/disapprove/{user_id}")
        
        if response.status_code == 200:
            return jsonify({"message": "User disapproved successfully!"}), 200
        else:
            return jsonify({"error": "Failed to disapprove user in Microservice 1"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@AboutCourse.route('/userCourses/<int:user_id>', methods=['GET'])
def get_user_courses(user_id):
    try:
        # Fetch enrollments for the user
        enrollments = Enrollment.query.filter_by(user_id=user_id).all()
        if not enrollments:
            return jsonify({"message": "No courses found for this user"}), 404

        # Collect course performance details
        course_details = []
        for enrollment in enrollments:
            course = Course.query.get(enrollment.course_id)
        
            course_progress = CourseProgress.query.filter_by(user_id=user_id, course_id=enrollment.course_id).first()
            # print(course_progress)
            if course:
                # Check course progress status, default if none
                progress_status = course_progress.status if course_progress else 'Not Started'

                course_details.append({
                    "course_id": course.id,
                    "title": course.title,
                    "description": course.description,
                    "instructor": course.instructor,
                    "status": enrollment.status,
                    "is_completed": enrollment.is_completed,
                    "enrolled_date": str(enrollment.enrolled_date),
                    "progress_status": progress_status,  # Add course progress here
                    "completion_percentage":course_progress.completion_percentage if course_progress else 0
                })

        return jsonify(course_details), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@AboutCourse.route('/employee-course-progress/<int:user_id>/<int:course_id>', methods=['GET'])
def get_employee_course_progress(user_id, course_id):
    try:
        # Fetch user details from the first microservice
        first_microservice_url = f'http://localhost:5001/users/{user_id}'  # Assuming user details endpoint
        response = requests.get(first_microservice_url)

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch user details from the first microservice."}), response.status_code

        user = response.json()

        if user.get('role') != 'Employee':
            return jsonify({"error": "User is not an employee."}), 400

        # Fetch course progress details from the database
        course_progress = CourseProgress.query.filter_by(user_id=user_id, course_id=course_id).first()

        if not course_progress:
            return jsonify({"error": "No progress found for this user in the specified course."}), 404

        progress_data = {
            "name": user.get('name'),
            "email": user.get('email'),
            "course_id": course_id,
            "completion_percentage": course_progress.completion_percentage,
            "status": course_progress.status,
            "last_accessed": course_progress.last_accessed.strftime("%Y-%m-%d %H:%M:%S") if course_progress.last_accessed else None
        }

        return jsonify(progress_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
EXCLUDED_ROLES = {"Manager", "HR", "Instructor"}

@AboutCourse.route('/course/<int:course_id>/enrollments', methods=['GET'])
def get_enrollment_status(course_id):
    try:
        # Fetch all users from the first microservice
        response = requests.get('http://localhost:5001/users')
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch users"}), 500
        
        all_users = response.json()

        # Fetch enrolled users for the given course_id from the database
        enrolled_users = Enrollment.query.filter_by(course_id=course_id).all()
        enrolled_user_ids = {enrollment.user_id for enrollment in enrolled_users}

        enrolled = []
        not_enrolled = []

        for user in all_users:
            # Skip users with roles Manager, HR, and Instructor
            if user["role"] in EXCLUDED_ROLES:
                continue

            user_data = {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "isVerified": user["isVerified"]
            }

            if user["id"] in enrolled_user_ids:
                enrolled.append(user_data)
            else:
                not_enrolled.append(user_data)

        return jsonify({
            "enrolled_users": enrolled,
            "not_enrolled_users": not_enrolled
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
