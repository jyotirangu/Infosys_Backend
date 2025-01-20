from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from .model import db
from .model import User, Course, Enrollment, AuditTrail, Module, Quiz, QuizResult, CourseProgress
from datetime import datetime


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
            progress = CourseProgress.query.filter_by(user_id=user_id, module_id=module.id).first()

            # Prepare module data
            module_data = {
                "id": module.id,
                "title": module.title,
                "description": module.description,
                "course": {
                    "id": module.course.id,
                    "title": module.course.title,
                    "description": module.course.description
                },
                "progress": progress.completion_status if progress else "Not Started",
                "score": progress.score if progress else None
            }

            response.append(module_data)

        return jsonify({"modules": response}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500




@ModuleQuiz.route('/api/modules/<int:module_id>/progress', methods=['PUT'])
def update_progress(module_id):
    try:
        data = request.get_json()
        new_progress = data.get("progress")

        if not new_progress or new_progress not in ["Not Started", "In Progress", "Completed"]:
            return jsonify({"error": "Invalid progress value"}), 400

        module = Module.query.get(module_id)
        if not module:
            return jsonify({"error": "Module not found"}), 404

        module.progress = new_progress
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
            "quizzes": [
                {
                    "id": quiz.id,
                    "question": quiz.question,
                    "options": quiz.options,  # JSON format options
                    "marks": quiz.marks
                }
                for quiz in module.quizzes
            ]
        }

        return jsonify({"module": module_details}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# SHAI HAI UPAR WLA

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
        answers = data.get("answers")  # Answers provided by the user

        # Validate user existence
        user = User.query.get(user_id)
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

        for quiz in module.quizzes:
            quiz_id = quiz.id
            user_answer = answers.get(str(quiz_id))
            correct_answer = quiz.correct_answer

            # Check correctness and calculate score
            correct_answers[str(quiz_id)] = correct_answer
            is_correct[str(quiz_id)] = user_answer == correct_answer
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
            quiz_id=module_id,
            score=total_score,
            status=status,
            attempted_at=datetime.now(),
            total_marks=total_marks,
            answers=answers,
            correct_answers=correct_answers,
            is_correct=is_correct
        )
        db.session.add(quiz_result)

        # Update or create CourseProgress entry
        course_progress = CourseProgress.query.filter_by(user_id=user_id, course_id=module.course_id, module_id=module_id).first()
        if course_progress:
            # Update existing progress
            course_progress.completion_status = status
            course_progress.completion_date = datetime.now()
            course_progress.score = total_score
            course_progress.corrected += corrected_count  # Keep cumulative count
            course_progress.incorrected += incorrected_count
            course_progress.skipped += skipped_count
        else:
            # Create new progress entry
            course_progress = CourseProgress(
                user_id=user_id,
                course_id=module.course_id,
                module_id=module_id,
                completion_status=status,
                completion_date=datetime.now(),
                score=total_score,
                corrected=corrected_count,
                incorrected=incorrected_count,
                skipped=skipped_count
            )
            db.session.add(course_progress)

        db.session.commit()

        return jsonify({
            "message": "Quiz submitted successfully!",
            "result": {
                "user_id": user_id,
                "module_id": module_id,
                "score": total_score,
                "status": status,
                "total_marks": total_marks,
                "answers": answers,
                "correct_answers": correct_answers,
                "is_correct": is_correct,
                "corrected_count": corrected_count,
                "incorrected_count": incorrected_count,
                "skipped_count": skipped_count
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Create a new route for employee-specific progress

@ModuleQuiz.route('/api/employee-progress-detail/<user_id>/<courseid>', methods=['GET'])
def get_employee_progress_detail(user_id,courseid):
    print(courseid);
    progress = CourseProgress.query.filter_by(user_id=user_id,course_id=courseid).all()

    if not progress:
        return jsonify({"message": "No progress data found for the user"}), 404

    result = []
    for progress_item in progress:
        module = Module.query.filter_by(id=progress_item.module_id).first()
        course = Course.query.filter_by(id=progress_item.course_id).first()

        result.append({
            "user_id": user_id,
            "course_id": course.id,
            "course_title": course.title,
            "module_id": module.id,
            "module_title": module.title,
            "completion_status": progress_item.completion_status,
            "score": progress_item.score,
            "completion_date": progress_item.completion_date
        })

    return jsonify({"progress": result}), 200


@ModuleQuiz.route('/api/course-progress', methods=['GET'])
def get_course_progress():
    user_id = request.args.get('user_id')
    course_id = request.args.get('course_id')

    if not user_id or not course_id:
        return jsonify({"message": "Missing parameters (user_id or course_id)"}), 400

    # Query all modules for the given course
    modules = Module.query.filter_by(course_id=course_id).all()

    if not modules:
        return jsonify({"message": "No modules found for the specified course"}), 404

    # Query the CourseProgress for the user and course (can be empty if no progress made yet)
    progress = CourseProgress.query.filter_by(user_id=user_id, course_id=course_id).all()
    
    result = []
    for module in modules:
        # Find the user's progress for the current module (if any)
        user_progress = next((p for p in progress if p.module_id == module.id), None)
        module_progress = {
            "completion_status": user_progress.completion_status if user_progress else "Not Started",
            "completion_date": user_progress.completion_date if user_progress else None,
            "score": user_progress.score if user_progress else 0,
            "corrected": user_progress.corrected if user_progress else 0,
            "incorrected": user_progress.incorrected if user_progress else 0,
            "skipped": user_progress.skipped if user_progress else 0
        }

        result.append({
            "user_id": user_id,
            "course_id": course_id,
            "module_id": module.id,
            "title": module.title,
            "description": module.description,
            "progress": module_progress  # Will show user progress if available
        })

    return jsonify({"modules": result}), 200