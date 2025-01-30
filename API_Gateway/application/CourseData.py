from flask import Blueprint, jsonify, request
import requests

AboutCourse = Blueprint('AboutCourse', __name__)

@AboutCourse.route('/courses/<int:user_id>', methods=['GET'])
def get_courses(user_id):
    try:
        # Forward the request to the microservice
        response = requests.get(f"http://127.0.0.1:5002/courses/{user_id}")
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the courses service", "details": str(e)}), 500
    
@AboutCourse.route('/addCourse', methods=['POST'])
def add_course():
    try:
        data = request.get_json()
        print(data)
        # Forward the request to the microservice
        response = requests.post("http://127.0.0.1:5002/addCourse", json=data)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the add course service", "details": str(e)}), 500

@AboutCourse.route('/instructor', methods=['GET'])
def get_instructors():
    try:
        # Forward the request to the microservice
        response = requests.get("http://127.0.0.1:5002/instructor")
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the instructor service", "details": str(e)}), 500
    
@AboutCourse.route("/editCourse/<int:course_id>", methods=["POST", "PUT"])
def edit_course(course_id):
    try:
        data = request.get_json()
        user_id = data.get("userId")
        course_data = data.get("courseData")

        # Forward the request to the microservice
        response = requests.put(f"http://127.0.0.1:5002/editCourse/{course_id}", json=data)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the edit course service", "details": str(e)}), 500

@AboutCourse.route('/course/enrolledcourses/<int:user_id>', methods=['GET'])
def get_enrolled_courses(user_id):
    try:
        # Forward the request to the microservice
        response = requests.get(f"http://127.0.0.1:5002/course/enrolledcourses/{user_id}")
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the enrolled courses service", "details": str(e)}), 500

@AboutCourse.route('/enroll', methods=['POST'])
def enroll_in_course():
    try:
        data = request.get_json()

        # Forward the request to the microservice
        response = requests.post("http://127.0.0.1:5002/enroll", json=data)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the enroll service", "details": str(e)}), 500

@AboutCourse.route('/course/completed', methods=['POST'])
def complete_course():
    complete_course_service_url = "http://127.0.0.1:5002/course/completed"
    
    try:
        # Forward the incoming data to the complete course service
        response = requests.post(complete_course_service_url, json=request.get_json())
        
        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the course completion service", "details": str(e)}), 500
    
@AboutCourse.route('/course/audittrail', methods=['POST'])
def log_audit_trail():
    log_audit_trail_service_url = "http://127.0.0.1:5002/course/audittrail"
    
    try:
        # Forward the incoming data to the log audit trail service
        response = requests.post(log_audit_trail_service_url, json=request.get_json())
        
        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the audit trail service", "details": str(e)}), 500


@AboutCourse.route('/course/audittrail', methods=['GET'])
def get_course_audit_trail():
    get_course_audit_trail_service_url = "http://127.0.0.1:5002/course/audittrail"
    
    try:
        # Forward the request to the get course audit trail service
        response = requests.get(get_course_audit_trail_service_url)
        
        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the audit trail service", "details": str(e)}), 500


@AboutCourse.route('/course/users/<int:course_id>', methods=['GET'])
def get_users_for_course(course_id):
    get_users_for_course_service_url = f"http://127.0.0.1:5002/course/users/{course_id}"
    
    try:
        # Forward the request to the get users for course service
        response = requests.get(get_users_for_course_service_url)
        
        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the get users for course service", "details": str(e)}), 500
    
@AboutCourse.route('/viewCourse/<int:user_id>/<int:course_id>', methods=['GET'])
def view_course(user_id, course_id):
    view_course_service_url = f"http://127.0.0.1:5002/viewCourse/{user_id}/{course_id}"
    
    try:
        # Forward the request to the view course details service
        response = requests.get(view_course_service_url)
        
        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the view course service", "details": str(e)}), 500
    
@AboutCourse.route('/users/unverified', methods=['GET'])
def get_unverified_users():
    get_unverified_users_service_url = "http://127.0.0.1:5002/users/unverified"
    
    try:
        # Forward the request to the get unverified users service
        response = requests.get(get_unverified_users_service_url)
        
        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the unverified users service", "details": str(e)}), 500

@AboutCourse.route('/users/approve/<int:user_id>', methods=['PATCH'])
def approve_user(user_id):
    approve_user_service_url = f"http://127.0.0.1:5002/users/approve/{user_id}"
    
    try:
        # Forward the request to the approve user service
        response = requests.patch(approve_user_service_url)
        
        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the approve user service", "details": str(e)}), 500

@AboutCourse.route('/users/disapprove/<int:user_id>', methods=['PATCH'])
def disapprove_user(user_id):
    disapprove_user_service_url = f"http://127.0.0.1:5002/users/disapprove/{user_id}"
    
    try:
        # Forward the request to the disapprove user service
        response = requests.patch(disapprove_user_service_url)
        
        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the disapprove user service", "details": str(e)}), 500

    
@AboutCourse.route('/course/<int:course_id>/enrollments', methods=['GET'])
def get_enrollment_status(course_id):
    enrollment_service_url = f"http://127.0.0.1:5002/course/{course_id}/enrollments"

    try:
        # Forward the request to the enrollment service
        response = requests.get(enrollment_service_url)

        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the enrollment service", "details": str(e)}), 500

@AboutCourse.route('/employee-course-progress/<int:user_id>/<int:course_id>', methods=['GET'])
def get_employee_enrollment_status(user_id, course_id):
    print(user_id)
    print(course_id)
    employee_service_url = f"http://127.0.0.1:5002/employee-course-progress/{user_id}/{course_id}"

    try:
        # Forward the request to the first microservice
        response = requests.get(employee_service_url)
        print(response)

        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the employee service", "details": str(e)}), 500

