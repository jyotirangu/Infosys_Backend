from flask import Blueprint, jsonify, request
import requests

Performance = Blueprint('Performance', __name__)

@Performance.route("/manager/performance", methods=["GET"])
def proxy_manager_performance():
    # Define the URL of the performance microservice for managers
    performance_service_url = "http://127.0.0.1:5002/manager/performance"
    
    try:
        # Forward the incoming GET request to the performance microservice
        response = requests.get(performance_service_url)
        
        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        # Handle any errors in communication with the microservice
        return jsonify({"error": "Failed to connect to the performance service", "details": str(e)}), 500


@Performance.route("/hr/performance", methods=["GET"])
def proxy_hr_performance():
    # Define the URL of the performance microservice for HR
    performance_service_url = "http://127.0.0.1:5002/hr/performance"
    
    try:
        # Forward the incoming GET request to the performance microservice
        response = requests.get(performance_service_url)
        
        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        # Handle any errors in communication with the microservice
        return jsonify({"error": "Failed to connect to the performance service", "details": str(e)}), 500
    
    
@Performance.route("/api/individual-performance/<int:team_member_id>", methods=["GET"])
def proxy_individual_performance(team_member_id):
    # Define the URL of the individual performance microservice
    performance_service_url = f"http://127.0.0.1:5002/api/individual-performance/{team_member_id}"
    
    try:
        # Forward the incoming GET request to the performance microservice
        response = requests.get(performance_service_url)
        
        # Return the response from the microservice to the client
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        # Handle any errors in communication with the microservice
        return jsonify({"error": "Failed to connect to the individual performance service", "details": str(e)}), 500
