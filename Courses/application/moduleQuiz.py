from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from .model import db
from .model import Course, Enrollment, AuditTrail, Module, Quiz, QuizResult, CourseProgress, PerformanceAnalytics
from datetime import datetime
from sqlalchemy.sql import func
import requests, json


# Create a Blueprint for course-related routes
ModuleQuiz = Blueprint('ModuleQuiz', __name__)

@ModuleQuiz.route('/api/modules', methods=['GET'])
def get_modules():
    try:
        # Get both user_id and course_id from the request
        user_id = request.args.get('user_id')
        course_id = request.args.get('course_id')

        if not user_id or not course_id:
            return jsonify({"error": "User ID and Course ID are required"}), 400

        # Fetch modules specific to the course
        modules = Module.query.filter_by(course_id=course_id).all()

        response = []

        for module in modules:
            # Fetch progress data for this user and module
            progress = CourseProgress.query.filter_by(user_id=user_id, course_id=course_id).first()

            # Prepare module data
            module_data = {
                "id": module.id,
                "title": module.title,
                "description": module.description,
                "objectives": module.objectives,
                "learning_points": module.learning_points,
                "completion_percentage": module.completion_percentage,
                "course": {
                    "id": module.course.id,
                    "title": module.course.title,
                    "description": module.course.description,
                },
                "progress": {
                    "completion_percentage": progress.completion_percentage if progress else 0.0,
                    "status": progress.status if progress else "Not Started",
                }
            }

            response.append(module_data)

        return jsonify({"modules": response}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@ModuleQuiz.route('/api/modules/<int:module_id>/progress', methods=['PUT'])
def update_progress(module_id):
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        completion_percentage = data.get("completion_percentage")
        status = data.get("status")

        if not user_id or completion_percentage is None or not status:
            return jsonify({"error": "User ID, completion percentage, and status are required"}), 400

        if status not in ["Not Started", "In Progress", "Completed"]:
            return jsonify({"error": "Invalid status value"}), 400

        # Fetch the module and user progress
        module = Module.query.get(module_id)
        if not module:
            return jsonify({"error": "Module not found"}), 404

        progress = CourseProgress.query.filter_by(user_id=user_id, course_id=module.course_id).first()

        if progress:
            progress.completion_percentage = completion_percentage
            progress.status = status
            progress.last_accessed = func.now()
        else:
            # Create a new progress entry if not exists
            new_progress = CourseProgress(
                user_id=user_id,
                course_id=module.course_id,
                completion_percentage=completion_percentage,
                status=status,
                last_accessed=func.now()
            )
            db.session.add(new_progress)

        db.session.commit()

        return jsonify({"message": "Progress updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ModuleQuiz.route('/module/<int:module_id>/details', methods=['GET'])
def get_module_details(module_id):
    try:
        # Fetch module details
        module = Module.query.get(module_id)
        if not module:
            return jsonify({"error": f"Module with ID {module_id} not found!"}), 404

        # Prepare module details with quizzes
        module_details = {
            "id": module.id,
            "title": module.title,
            "description": module.description,
            "objectives": module.objectives,
            "learning_points": module.learning_points,
            "completion_percentage": module.completion_percentage,
            "quizzes": [
                {
                    "id": quiz.id,
                    "question": quiz.question,
                    "options": quiz.options,
                    "marks": quiz.marks,
                    "weightage": quiz.weightage
                }
                for quiz in module.quizzes
            ]
        }

        return jsonify({"module": module_details}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

AUTH_SERVICE_URL = "http://localhost:5001" 

# Helper function to fetch user details from the authentication service
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

@ModuleQuiz.route('/module/<int:module_id>/submit-quiz', methods=['POST'])
def submit_quiz(module_id):
    try:
        # Fetch the module
        module = Module.query.get(module_id)
        if not module:
            return jsonify({"error": f"Module with ID {module_id} not found"}), 404

        # Get request data
        data = request.get_json()
        user_id = data.get("user_id")
        answers = data.get("answers") 
        time_spent = data.get("time_spent", 0)  

        # Validate user existence using the authentication service
        user = fetch_user_details(user_id)
        if not user:
            return jsonify({"error": f"User with ID {user_id} not found"}), 404

        # Initialize variables for quiz result
        total_score = 0
        total_marks = 0
        correct_answers = {}
        is_correct = {}
        corrected_count = 0
        incorrected_count = 0
        skipped_count = 0

        # Iterate over quizzes in the module
        for quiz in module.quizzes:
            quiz_id = quiz.id
            user_answer = answers.get(str(quiz_id))  # Get the user's answer for the quiz
            correct_answer = quiz.correct_answer

            # Handle answer types
            if isinstance(user_answer, str) and user_answer.lower() == "none":
                user_answer = None
            elif isinstance(user_answer, str):
                user_answer = str(user_answer)
            elif isinstance(user_answer, float):
                user_answer = float(user_answer)

            # Store correct answers and correctness status
            correct_answers[str(quiz_id)] = correct_answer
            is_correct[str(quiz_id)] = user_answer == correct_answer

            # Calculate score and update counts
            if user_answer == correct_answer:
                total_score += quiz.marks
                corrected_count += 1
            elif user_answer is None:
                skipped_count += 1
            else:
                incorrected_count += 1
            total_marks += quiz.marks

        # Determine quiz status
        status = "Passed" if total_score >= (0.5 * total_marks) else "Failed"

        # Save quiz result to the database
        quiz_result = QuizResult(
            user_id=user_id,
            module_id=module.id,
            score=total_score,
            status=status,
            attempted_at=datetime.now(),
            total_marks=total_marks,
            answers=json.dumps(answers),
            correct_answers=json.dumps(correct_answers),
            is_correct=json.dumps(is_correct),
            time_spent=time_spent,
            is_complete=True
        )
        db.session.add(quiz_result)

        # Update module completion percentage
        module_completion_percentage = (1 if status == "Passed" else 0)
        module.completion_percentage += module_completion_percentage

        # Update or create CourseProgress
        course_progress = CourseProgress.query.filter_by(user_id=user_id, course_id=module.course_id).first()
        if course_progress:
            course_progress.completion_percentage += (module_completion_percentage / len(module.course.modules)) * 100
            course_progress.last_accessed = datetime.now()
            course_progress.status = "Completed" if course_progress.completion_percentage >= 100 else "In Progress"
        else:
            course_progress = CourseProgress(
                user_id=user_id,
                course_id=module.course_id,
                completion_percentage=(module_completion_percentage / len(module.course.modules)) * 100,
                status="In Progress",
                last_accessed=datetime.now()
            )
            db.session.add(course_progress)

        # Update Performance Analytics
        performance = PerformanceAnalytics.query.filter_by(user_id=user_id, course_id=module.course_id).first()
        if performance:
            performance.quizzes_taken += 1
            performance.modules_completed += (1 if course_progress.completion_percentage >= 100 else 0)
            performance.total_score += total_score
            performance.average_score = performance.total_score / performance.quizzes_taken
        else:
            performance = PerformanceAnalytics(
                user_id=user_id,
                course_id=module.course_id,
                quizzes_taken=1,
                modules_completed=(1 if course_progress.completion_percentage >= 100 else 0),
                total_score=total_score,
                average_score=total_score
            )
            db.session.add(performance)

        db.session.commit()

        return jsonify({
            "message": "Quiz submitted successfully!",
            "result": {
                "user_id": user_id,
                "module_id": module.id,
                "score": total_score,
                "status": status,
                "total_marks": total_marks,
                "answers": answers,
                "correct_answers": correct_answers,
                "is_correct": is_correct,
                "corrected_count": corrected_count,
                "incorrected_count": incorrected_count,
                "skipped_count": skipped_count,
                "completion_percentage": course_progress.completion_percentage,
                "time_spent": time_spent
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@ModuleQuiz.route('/api/employee-progress-detail/<user_id>/<course_id>', methods=['GET'])
def get_employee_progress_detail(user_id, course_id):
    progress = CourseProgress.query.filter_by(user_id=user_id, course_id=course_id).all()

    if not progress:
        return jsonify({"message": "No progress data found for the user"}), 404

    result = []
    for progress_item in progress:
        module = Module.query.get(progress_item.module_id)
        if module:
            result.append({
                "user_id": user_id,
                "course_id": course_id,
                "module_id": module.id,
                "module_title": module.title,
                "completion_status": progress_item.status,
                "completion_percentage": progress_item.completion_percentage,
                "last_accessed": progress_item.last_accessed
            })

    return jsonify({"progress": result}), 200


@ModuleQuiz.route('/api/course-progress', methods=['GET'])
def get_course_progress():
    user_id = request.args.get('user_id')
    course_id = request.args.get('course_id')
    
    if not user_id or not course_id:
        return jsonify({"error": "User ID or Course ID is missing"}), 400

    # Query all modules for the course
    modules = db.session.query(Module).filter(Module.course_id == course_id).all()
    module_ids = {module.id for module in modules}  # Store module IDs for quick filtering

    # Query quiz results for the user
    quiz_results = db.session.query(
        QuizResult.module_id,
        QuizResult.status,
        QuizResult.score,
        QuizResult.total_marks,
    ).filter(QuizResult.user_id == user_id).all()

    # Filter quiz results to include only those related to the given course_id
    quiz_result_dict = {
        result.module_id: {'status': result.status, 'score': result.score, 'total_marks': result.total_marks}
        for result in quiz_results if result.module_id in module_ids
    }

    # Query the CourseProgress for the user and course
    progress = CourseProgress.query.filter_by(user_id=user_id, course_id=course_id).first()
    
    # Calculate total quiz score and percentage for the course only
    total_score = sum(result['score'] for result in quiz_result_dict.values())
    total_marks = sum(result['total_marks'] for result in quiz_result_dict.values())
    quiz_percentage = (total_score / total_marks * 100) if total_marks > 0 else 0.0

    # Include quiz performance in Course_progress
    module_progress = {
        "completion_status": progress.status if progress else "Not Started",
        "completion_percentage": progress.completion_percentage if progress else 0.0,
        "last_accessed": progress.last_accessed if progress else None,
        "total_score": total_score,
        "total_marks": total_marks,
        "quiz_percentage": round(quiz_percentage, 2)  # Rounded to 2 decimal places
    }

    # Prepare the module-wise response
    response = []
    for module in modules:
        module_status = quiz_result_dict.get(module.id, {}).get("status", "Not Started")
        response.append({
            "module_id": module.id,
            "title": module.title,
            "description": module.description,
            "status": module_status,
        })

    return jsonify({
        "modules": response,
        "Course_progress": module_progress
    })
