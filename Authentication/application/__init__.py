from flask import Flask
from flask import Blueprint, jsonify, request
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import requests
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
)

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello World</p>"


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



jwt = JWTManager(app)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})


# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:1234@localhost:5432/Infosys"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:1234@localhost:5432/InfosysAuth"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# It’s not specifically related to JWTs but is essential for overall app security. Server side secret key
app.config['SECRET_KEY'] = 'your_secret_key'
# The JWT_SECRET_KEY is used to generate a secure signature for JWTs, allowing the server to verify the authenticity of tokens. It is making token
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'

# db = SQLAlchemy(app)
db.init_app(app)
migrate = Migrate(app, db)

# Create the database tables if they don't exist
with app.app_context():
    db.create_all()

# Route to sign up
@app.route("/register", methods=["POST"])
def signup():
    try:
        # Parse incoming JSON data
        data = request.get_json()       # This means I'm taking data in JSON format only, for other format it will deny or show error
        
        # Extract and validate fields
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        role = data.get("role")  
        answer = data.get("answer")
        

        if not name or not email or not password:
            return jsonify({"error": "Name, Email, and Password are required!"}), 400

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create a new user
        new_user = User(name=name, email=email, password=hashed_password, role=role, isVerified="False", answer=answer)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User created successfully!", "user": {
            "name": name,
            "email": email,
            "role": role
        }}), 201
    except Exception as e:
        return jsonify({"error":str(e)}),500

  
# Route to Login

@app.route("/login", methods=["POST"])
def login():
    
        # Parse incoming JSON data
        data = request.get_json()
    
        # Extract and validate fields
        email = data.get("email")
        password = data.get("password")
        role = data.get("role")
        
        print(email)
        print(password)
        
        if not email or not password or not role:
            return jsonify({"error": "Email, Password and role are required!"}), 400
        
        
        # Query user from the database
        user = User.query.filter_by(email=email).first()
        # print(hashed_password)
        # print(user.password)

        if not user:
            return jsonify({"error": "User not found!"}), 404

        # Verify role
        if user.role != role:
            return jsonify({"error": f"Role mismatch: Expected {user.role}, got {role}"}), 403

        # Check password
        # Check the hashed password
        if not check_password_hash(user.password, password):
            return jsonify({"error": "Invalid password!"}), 401
        
        # Verify the Password
        if( user.isVerified == "False"):
            return jsonify({"error": "Not Verified"}), 401

        # The token encodes user information (in this case, user.id) and signs it using the JWT_SECRET_KEY. The client (e.g., a frontend app) can use this token to authenticate subsequent requests.
        access_token = create_access_token(identity=user.id)   
     
        # Login successful
        return jsonify({"token": access_token, "message": "Login successful!", "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}}), 200
    


# Route to forget password

@app.route("/forgetpassword", methods=["POST"])
def forgetpassword():
    # Parse incoming JSON data
    data = request.get_json()
        
    # Extract and validate fields
    email = data.get("email")
    answer = data.get("answer")
    newPassword = data.get("newPassword")
    
    hashed_password = generate_password_hash(newPassword)
    
    if not email or not answer:
        return jsonify({"error": "Email and security answer are required!"}), 400
    
    # Query user from the database
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found!"}), 404

    # Verify the answer
    if user.answer != answer:
        return jsonify({"error": "Security answer is incorrect!"}), 403
    
    # Update the password in the database
    user.password = hashed_password
    db.session.commit()
    
    return jsonify({"message": "Password updated successfully!"}), 200


# Route to fetch all users
@app.route('/users', methods=['GET'])
def get_all_users():
    """
    Fetch all users from the database.
    """
    users = User.query.all()
    user_list = [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "isVerified": user.isVerified,
            "answer": user.answer
        }
        for user in users
    ]
    return jsonify(user_list), 200

# Route to fetch a user by ID
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """
    Fetch a specific user by ID.
    """
    user = User.query.filter_by(id=user_id).first()
    if user:
        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "isVerified": user.isVerified,
            "answer": user.answer
        }
        print(user_data)
        return jsonify(user_data), 200
        
    else:
        return jsonify({"error": f"User with ID {user_id} not found!"}), 404
    

@app.route('/users/role/Employee', methods=['GET'])
def get_employees():
    try:
        # Fetch all users with the 'Employee' role
        employees = User.query.filter_by(role='Employee').all()

        if not employees:
            return jsonify({"message": "No employees found"}), 404

        # Convert employee objects to a list of dictionaries
        employee_list = [
            {"id": employee.id, "name": employee.name, "email": employee.email, "role": employee.role}
            for employee in employees
        ]
        
        return jsonify(employee_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to fetch all unverified users
@app.route('/users/unverified', methods=['GET'])
def get_unverified_users():
    try:
        # Fetch all users with 'isVerified' as 'False'
        unverified_users = User.query.filter_by(isVerified="False").all()

        if not unverified_users:
            return jsonify({"message": "No unverified users found"}), 404

        # Convert user objects to a list of dictionaries
        unverified_user_list = [
            {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
            for user in unverified_users
        ]
        
        return jsonify(unverified_user_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to approve a user
@app.route('/users/approve/<int:user_id>', methods=['PATCH'])
def approve_user(user_id):
    try:
        # Fetch the user by ID
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Update the 'isVerified' status to 'True'
        user.isVerified = "True"
        db.session.commit()
        return jsonify({"message": "User approved successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to disapprove or reset a user
@app.route('/users/disapprove/<int:user_id>', methods=['PATCH'])
def disapprove_user(user_id):
    try:
        # Fetch the user by ID
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Update the 'isVerified' status to 'False'
        user.isVerified = "False"
        db.session.commit()
        return jsonify({"message": "User disapproved successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
# Base URL of Courses Microservice
COURSES_MICROSERVICE_URL = "http://localhost:5002"

# Profile route
@app.route('/profile/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    try:
        # Fetch user details from Authentication Microservice
        user = User.query.get(user_id)
        print(user)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Prepare user profile data
        user_details = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "isVerified": user.isVerified
        }

        # Fetch user's course performance from Courses Microservice
        response = requests.get(f"{COURSES_MICROSERVICE_URL}/userCourses/{user_id}")
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch data from Courses Microservice"}), response.status_code

        course_performance = response.json()

        # Combine profile and course data
        profile_data = {
            "user_details": user_details,
            "course_performance": course_performance
        }

        return jsonify(profile_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True,port=5001)