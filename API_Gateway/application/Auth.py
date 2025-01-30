from flask import Blueprint, jsonify, request
import requests

auth = Blueprint('auth', __name__)


@auth.route("/login", methods=["POST"])
def proxy_login():
    # Define the URL of the login microservice
    login_service_url = "http://127.0.0.1:5001/login"
    
    try:
        # Forward the incoming JSON data to the login microservice
        response = requests.post(login_service_url, json=request.get_json())
        print(response)
        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        # Handle any errors in communication with the microservice
        return jsonify({"error": "Failed to connect to the login service", "details": str(e)}), 500
    



@auth.route("/register", methods=["POST"])
def register_proxy():
    # Define the URL of the register microservice
    register_service_url = "http://127.0.0.1:5001/register"
    
    try:
        # Forward the incoming JSON data to the register microservice
        response = requests.post(register_service_url, json=request.get_json())
        
        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        # Handle any errors in communication with the microservice
        return jsonify({"error": "Failed to connect to the register service", "details": str(e)}), 500


@auth.route("/forgetpassword", methods=["POST"])
def forget_password_proxy():
    # Define the URL of the forgetpassword microservice
    forget_password_service_url = "http://127.0.0.1:5001/forgetpassword"
    
    try:
        # Forward the incoming JSON data to the forgetpassword microservice
        response = requests.post(forget_password_service_url, json=request.get_json())
        
        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        # Handle any errors in communication with the microservice
        return jsonify({"error": "Failed to connect to the forgetpassword service", "details": str(e)}), 500
    

@auth.route('/profile/<int:user_id>', methods=['GET'])
def get_user_profile_proxy(user_id):
    # Define URLs for Authentication and Courses Microservices
    auth_service_url = f"http://127.0.0.1:5001/users/{user_id}"
    courses_service_url = f"http://127.0.0.1:5002/userCourses/{user_id}"

    try:
        # Fetch user details from Authentication Microservice
        auth_response = requests.get(auth_service_url)
        if auth_response.status_code != 200:
            return jsonify({"error": "Failed to fetch user details", "details": auth_response.text}), auth_response.status_code
        user_details = auth_response.json()

        # Fetch user's course performance from Courses Microservice
        courses_response = requests.get(courses_service_url)
        if courses_response.status_code != 200:
            return jsonify({"error": "Failed to fetch course performance", "details": courses_response.text}), courses_response.status_code
        course_performance = courses_response.json()

        # Combine profile and course data
        profile_data = {
            "user_details": user_details,
            "course_performance": course_performance
        }

        return jsonify(profile_data), 200

    except requests.exceptions.RequestException as e:
        # Handle any communication errors with the microservices
        return jsonify({"error": "Failed to connect to one of the services", "details": str(e)}), 500
    except Exception as e:
        # Handle any other unexpected errors
        return jsonify({"error": str(e)}), 500

