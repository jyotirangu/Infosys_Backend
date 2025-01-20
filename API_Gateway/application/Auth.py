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