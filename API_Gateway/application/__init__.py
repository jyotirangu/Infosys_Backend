from flask import Flask, request, jsonify
import requests

from flask_cors import CORS


app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

with app.app_context():
    from .Auth import auth
    from .CourseData import AboutCourse
    from .ModuleQuiz import ModuleQuiz
    from .Performance import Performance 

# Register the Blueprint for the artifact routes   
app.register_blueprint(auth)
app.register_blueprint(AboutCourse)
app.register_blueprint(ModuleQuiz)
app.register_blueprint(Performance)

@app.route("/")
def hello_world():
    return "<p>Hello World</p>"

if __name__ == "__main__":
    app.run(debug=True, port=5000)
