from flask import Flask
from flask import Blueprint, jsonify, request
from flask_migrate import Migrate
from flask_cors import CORS
from .model import db
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
)

app = Flask(__name__)


# Create the database tables if they don't exist
with app.app_context():
    from .courseContent import AboutCourse
    
# Register the Blueprint for the artifact routes   
app.register_blueprint(AboutCourse)


@app.route("/")
def hello_world():
    return "<p>Hello World</p>"

# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime
# from sqlalchemy import func

# db = SQLAlchemy()

jwt = JWTManager(app)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:1234@localhost:5432/Infosys"
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
    
if __name__ == "__main__":
    app.run(debug=True, port=5002)
