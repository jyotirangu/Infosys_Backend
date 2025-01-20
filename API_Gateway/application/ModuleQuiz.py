from flask import Blueprint, jsonify, request
import requests

ModuleQuiz = Blueprint('ModuleQuiz', __name__)

# Route to get modules for a specific course
@ModuleQuiz.route("/api/modules", methods=["GET"])
def get_modules():
    try:
        # Get both user_id and course_id from the request
        user_id = request.args.get('user_id')
        course_id = request.args.get('course_id')

        if not user_id or not course_id:
            return jsonify({"error": "User ID and Course ID are required"}), 400

        # Define the URL of the module microservice
        module_service_url = "http://127.0.0.1:5003/api/modules"
        
        # Forward the incoming request data to the module microservice
        response = requests.get(module_service_url, params={'user_id': user_id, 'course_id': course_id})
        
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the module service", "details": str(e)}), 500

# Route to update progress for a specific module
@ModuleQuiz.route('/api/modules/<int:module_id>/progress', methods=['PUT'])
def update_progress(module_id):
    try:
        data = request.get_json()
        new_progress = data.get("progress")

        if not new_progress or new_progress not in ["Not Started", "In Progress", "Completed"]:
            return jsonify({"error": "Invalid progress value"}), 400

        # Define the URL of the progress microservice
        progress_service_url = f"http://127.0.0.1:5003/api/modules/{module_id}/progress"
        
        # Forward the incoming request data to the progress microservice
        response = requests.put(progress_service_url, json={'progress': new_progress})
        
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the progress service", "details": str(e)}), 500

# Route to get details of a specific module
@ModuleQuiz.route('/module/<int:module_id>/details', methods=['GET'])
def get_module_details(module_id):
    try:
        # Define the URL of the module details microservice
        module_details_service_url = f"http://127.0.0.1:5003/module/{module_id}/details"
        
        # Forward the incoming request to the module details microservice
        response = requests.get(module_details_service_url)
        
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the module details service", "details": str(e)}), 500

# Route to submit the quiz for a specific module
@ModuleQuiz.route('/module/<int:module_id>/submit-quiz', methods=['POST'])
def submit_quiz(module_id):
    try:
        # Define the URL of the quiz submission microservice
        quiz_submission_service_url = f"http://127.0.0.1:5003/module/{module_id}/submit-quiz"
        
        # Forward the incoming request data to the quiz submission microservice
        response = requests.post(quiz_submission_service_url, json=request.get_json())
        
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the quiz submission service", "details": str(e)}), 500

# Route to get employee-specific progress details
@ModuleQuiz.route('/api/employee-progress-detail/<user_id>/<courseid>', methods=['GET'])
def get_employee_progress_detail(user_id, courseid):
    try:
        # Define the URL of the employee progress microservice
        employee_progress_service_url = f"http://127.0.0.1:5003/api/employee-progress-detail/{user_id}/{courseid}"
        
        # Forward the incoming request to the employee progress microservice
        response = requests.get(employee_progress_service_url)
        
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the employee progress service", "details": str(e)}), 500

# Route to get course progress details
@ModuleQuiz.route('/api/course-progress', methods=['GET'])
def get_course_progress():
    try:
        user_id = request.args.get('user_id')
        course_id = request.args.get('course_id')

        if not user_id or not course_id:
            return jsonify({"message": "Missing parameters (user_id or course_id)"}), 400

        # Define the URL of the course progress microservice
        course_progress_service_url = f"http://127.0.0.1:5003/api/course-progress"
        
        # Forward the incoming request data to the course progress microservice
        response = requests.get(course_progress_service_url, params={'user_id': user_id, 'course_id': course_id})
        
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to the course progress service", "details": str(e)}), 500