import requests
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from .model import PerformanceAnalytics, CourseProgress, Enrollment, db, Course, QuizResult, Quiz

Performance = Blueprint('performance', __name__)

MICROSERVICE_1_BASE_URL = "http://127.0.0.1:5001" 


@Performance.route('/manager/performance', methods=['GET'])
def get_manager_performance():
    performance_data = PerformanceAnalytics.query.all()
    print(performance_data)

    # Extract user IDs for batch processing
    user_ids = [data.user_id for data in performance_data]

    # Fetch user details from Microservice 1 using the new route
    user_data = {}
    for user_id in user_ids:
        try:
            user_response = requests.get(f"{MICROSERVICE_1_BASE_URL}/users/{user_id}")
            if user_response.status_code == 200:
                user = user_response.json()
                user_data[user['id']] = user
            else:
                print(f"Error fetching user {user_id}: {user_response.json()['error']}")
        except Exception as e:
            print(f"Failed to fetch user {user_id}: {str(e)}")

    # Organize courses by user
    result = {}
    for data in performance_data:
        # Fetch course details from the Course schema
        course = Course.query.filter_by(id=data.course_id).first()
        if not course:
            continue

        user = user_data.get(data.user_id, {})
        
        # Create a user entry if it doesn't exist in the result dictionary
        if data.user_id not in result:
            result[data.user_id] = {
                "user_id": data.user_id,
                "user_name": user.get("name"),
                "user_email": user.get("email"),
                "courses": []
            }

        result[data.user_id]["courses"].append({
            "course_id": course.course_id,
            "course_title": course.title,
            "course_description": course.description,
            "detailed_description": course.detailed_description,
            "instructor": course.instructor,
            "start_date": course.start_date,
            "end_date": course.end_date,
            "duration": course.duration,
            "created_at": course.created_at,
            "total_score": data.total_score,
            "average_score": data.average_score
        })

    # Convert the result dictionary to a list of values for the final response
    return jsonify(list(result.values())), 200


@Performance.route('/hr/performance', methods=['GET'])
def get_hr_performance():
    # Fetch performance trends from the second microservice (using db)
    trends = db.session.query(
        PerformanceAnalytics.course_id,
        func.avg(PerformanceAnalytics.average_score).label("average_score"),
        func.sum(PerformanceAnalytics.total_score).label("total_score"),
        func.count(PerformanceAnalytics.user_id).label("total_employees")
    ).group_by(PerformanceAnalytics.course_id).all()
    
    course_id = request.args.get('courseId')
    user_id = request.args.get('userId')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')

    # Base query
    query = db.session.query(
        Enrollment.user_id,
        Enrollment.course_id,
        CourseProgress.completion_percentage,
        CourseProgress.status
    ).join(CourseProgress, Enrollment.course_id == CourseProgress.course_id)

    # Apply filters
    if course_id:
        query = query.filter(Enrollment.course_id == course_id)
    if user_id:
        query = query.filter(Enrollment.user_id == user_id)
    if start_date and end_date:
        query = query.filter(
            CourseProgress.status.between(start_date, end_date)  # Assuming `status` stores the date
        )

    detailed_performance = query.all()     

    # Fetch top performers from the second microservice (using db)
    top_performers = (
        db.session.query(
            PerformanceAnalytics.user_id,
            func.sum(PerformanceAnalytics.total_score).label("total_score")
        )
        .group_by(PerformanceAnalytics.user_id)
        .order_by(func.sum(PerformanceAnalytics.total_score).desc())
        .limit(10)
        .all()
    )

    # Fetch all user IDs and course IDs from detailed performance
    user_ids = list(set([data.user_id for data in detailed_performance]))
    course_ids = list(set([data.course_id for data in detailed_performance]))

    # Initialize user_data dictionary to store user details from Microservice 1
    user_data = {}

    # Fetch user data from Microservice 1 for each user
    for user_id in user_ids:
        try:
            user_response = requests.get(f"{MICROSERVICE_1_BASE_URL}/users/{user_id}")
            if user_response.status_code == 200:
                user = user_response.json()
                user_data[user['id']] = user
            else:
                print(f"Error fetching user {user_id}: {user_response.json()['error']}")
        except Exception as e:
            print(f"Failed to fetch user {user_id}: {str(e)}")

    # Fetch course details from the second microservice using the schema in models.py
    courses = db.session.query(Course).filter(Course.id.in_(course_ids)).all()

    # Map course data
    course_data = {course.id: course for course in courses}

    # Calculate metrics such as active vs. completed courses and quiz scores
    user_course_metrics = {}
    for performance in detailed_performance:
        user_id = performance.user_id
        if user_id not in user_course_metrics:
            user_course_metrics[user_id] = {
                "completed_courses": 0,
                "active_courses": 0,
                "total_quiz_scores": 0,
                "total_courses": 0
            }

        if performance.status == "Completed":
            user_course_metrics[user_id]["completed_courses"] += 1
        else:
            user_course_metrics[user_id]["active_courses"] += 1

        user_course_metrics[user_id]["total_courses"] += 1

        # Assuming quiz scores are tracked separately
        quiz_scores = db.session.query(func.sum(QuizResult.score)).filter_by(user_id=user_id).scalar()
        user_course_metrics[user_id]["total_quiz_scores"] = quiz_scores or 0

    # Fetch detailed performance and group by user_id and course_id
    detailed_performance = (
    db.session.query(
        Enrollment.user_id,
        Enrollment.course_id,
        CourseProgress.completion_percentage,
        CourseProgress.status
    )
    .join(CourseProgress, Enrollment.course_id == CourseProgress.course_id)
    .group_by(Enrollment.user_id, Enrollment.course_id, CourseProgress.completion_percentage, CourseProgress.status)  # Add to GROUP BY
    .all()
)

    # After fetching the data, process it to remove duplicates
    unique_performance = {}
    for performance in detailed_performance:
        user_id = performance.user_id
        course_id = performance.course_id

        if user_id not in unique_performance:
            unique_performance[user_id] = {}

        # Only store the most recent status and completion_percentage for each user-course combination
        unique_performance[user_id][course_id] = {
            "completion_percentage": performance.completion_percentage,
            "status": performance.status
        }

    # Now format the result to avoid duplicates and include necessary data
    formatted_performance = [
        {
            "user_id": user_id,
            "user_name": user_data.get(user_id, {}).get("name"),
            "courses": [
                {
                    "course_id": course_id,
                    "course_title": course_data.get(course_id, {}).title if course_data.get(course_id) else None,
                    "Start_date": course_data.get(course_id, {}).start_date if course_data.get(course_id) else None,
                    "End_date": course_data.get(course_id, {}).end_date if course_data.get(course_id) else None,
                    "completion_percentage": data["completion_percentage"],
                    "status": data["status"],
                }
                for course_id, data in courses.items()
            ],
            "metrics": user_course_metrics.get(user_id, {})
        }
        for user_id, courses in unique_performance.items()
    ]

    # Organize data by user and course details
    result = {
        "trends": [
            {
                "course_id": trend.course_id,
                "course_title": course_data.get(trend.course_id, {}).title if course_data.get(trend.course_id) else None,
                "average_score": trend.average_score,
                "total_score": trend.total_score,
                "total_employees": trend.total_employees
            }
            for trend in trends
        ],
        "top_performers": [
            {
                "user_id": performer.user_id,
                "user_name": user_data.get(performer.user_id, {}).get("name"),
                "total_score": performer.total_score
            }
            for performer in top_performers
        ],
        "detailed_performance": formatted_performance
    }

    return jsonify(result), 200



@Performance.route('/api/individual-performance/<int:team_member_id>', methods=['GET'])
def get_individual_performance(team_member_id):
    try:
        # Fetch courses enrolled by the team member
        enrolled_courses = Enrollment.query.filter_by(user_id=team_member_id).all()
        
        # Fetch course progress
        course_progress = CourseProgress.query.filter_by(user_id=team_member_id).all()
        
        # Fetch quiz scores
        quiz_scores = QuizResult.query.filter_by(user_id=team_member_id).all()
        
        # Fetch active vs. completed courses
        active_courses = sum(1 for course in course_progress if course.status == 'In Progress')
        completed_courses = sum(1 for course in course_progress if course.status == 'Completed')
        
        # Construct response data
        data = {
            "team_member_id": team_member_id,
            "enrolled_courses": [{
                "course_id": course.course_id,
                
                "status": course.status
            } for course in enrolled_courses],
            "course_progress": [{
                "course_id": progress.course_id,
                "courseName":Course.query.filter_by(id=progress.course_id).first().title,
                "completion_percentage": progress.completion_percentage
            } for progress in course_progress],
            "quiz_scores": [{
                "module_id": quiz.module_id,
                "score": quiz.score
            } for quiz in quiz_scores],
            "active_courses": active_courses,
            "completed_courses": completed_courses
        }
        
        return jsonify({"status": "success", "data": data}), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
