from flask import Blueprint, request, jsonify
from modules import User, QuizScore, Achievement
from database import db
from datetime import datetime
import random

quiz_bp = Blueprint('quiz', __name__)

# Hardcoded Question Bank
QUESTIONS = [
    {
        "id": 1,
        "question": "Which activity typically uses the most water in a household?",
        "options": ["Showering", "Toilet flushing", "Laundry", "Dishwashing"],
        "correct": 1  # Toilet flushing (approx 24-27%)
    },
    {
        "id": 2,
        "question": "What is the optimal temperature for a refrigerator to save energy?",
        "options": ["0°C to 2°C", "3°C to 5°C", "6°C to 8°C", "Below 0°C"],
        "correct": 1 # 3-5 C
    },
    {
        "id": 3,
        "question": "How much energy do LED bulbs save compared to incandescent bulbs?",
        "options": ["10%", "25%", "50%", "At least 75%"],
        "correct": 3
    },
    {
        "id": 4,
        "question": "Leaving a tap running while brushing teeth wastes approximately how much water?",
        "options": ["1 Liter", "3 Liters", "6 Liters", "12 Liters"],
        "correct": 2 # ~6L/min
    },
    {
        "id": 5,
        "question": "Which of these is 'Vampire Power'?",
        "options": ["Power used by bats", "Energy from solar panels at night", "Standby power from plugged-in devices", "Power stolen by neighbors"],
        "correct": 2
    },
    {
        "id": 6,
        "question": "What is the most energy-efficient way to boil water?",
        "options": ["Electric Kettle", "Stove top pot", "Microwave", "Open fire"],
        "correct": 0
    },
    {
        "id": 7,
        "question": "Which appliance should you run only when full to save energy/water?",
        "options": ["Toaster", "Dishwasher", "Microwave", "TV"],
        "correct": 1
    },
    {
        "id": 8,
        "question": "What is a 'low-flow' showerhead designed to do?",
        "options": ["Make water colder", "Reduce water usage without losing pressure", "Increase water bill", "Filter out minerals"],
        "correct": 1
    },
    {
        "id": 9,
        "question": "Turning off the lights when leaving a room can save how much energy?",
        "options": ["None", "Very little", "Significant amounts over time", "It damages the switch"],
        "correct": 2
    },
    {
        "id": 10,
        "question": "What is the best way to defrost frozen food safely and efficiently?",
        "options": ["On the counter", "In the microwave", "In the fridge overnight", "In hot water"],
        "correct": 2
    },
    {
        "id": 11,
        "question": "Which uses less water for the same hygiene result?",
        "options": ["Items bath (full tub)", "5-minute shower", "10-minute shower", "Sponge bath"],
        "correct": 1
    }
]

@quiz_bp.route('/questions', methods=['GET'])
def get_questions():
    # Return 3 random questions
    selected = random.sample(QUESTIONS, 3)
    # Hide correct answer in response
    response_questions = []
    for q in selected:
        q_copy = q.copy()
        del q_copy['correct']
        response_questions.append(q_copy)
    return jsonify(response_questions)

@quiz_bp.route('/submit', methods=['POST'])
def submit_quiz():
    data = request.json
    user_id = data.get('user_id')
    answers = data.get('answers') # Dict of {question_id: selected_index}
    
    if not user_id or not answers:
        return jsonify({"error": "Missing data"}), 400
        
    score = 0
    total = len(answers)
    
    # Calculate score
    for q_id, selected in answers.items():
        # Find question
        question = next((q for q in QUESTIONS if q["id"] == int(q_id)), None)
        if question and question["correct"] == selected:
            score += 1
            
    # Save Score
    new_score = QuizScore(user_id=user_id, score=score, max_score=total)
    db.session.add(new_score)
    
    # Check for Achievements
    earned_achievements = []
    
    # 1. First Quiz
    if QuizScore.query.filter_by(user_id=user_id).count() == 1:
        add_achievement(user_id, "First Step", "🌱", "Completed your first conservation quiz!")
        earned_achievements.append("First Step")

    # 2. Perfect Score
    if score == total:
        # Check if already has it
        has_perf = Achievement.query.filter_by(user_id=user_id, name="Quiz Master").first()
        if not has_perf:
            add_achievement(user_id, "Quiz Master", "🧠", "Scored 100% on a quiz!")
            earned_achievements.append("Quiz Master")
            
    # 3. Consistency (3 quizzes taken)
    if QuizScore.query.filter_by(user_id=user_id).count() == 3:
         if not Achievement.query.filter_by(user_id=user_id, name="Consistent Learner").first():
            add_achievement(user_id, "Consistent Learner", "📚", "Completed 3 quizzes!")
            earned_achievements.append("Consistent Learner")

    db.session.commit()
    
    return jsonify({
        "score": score,
        "total": total,
        "achievements": earned_achievements
    })

def add_achievement(user_id, name, icon, desc):
    ach = Achievement(user_id=user_id, name=name, icon=icon, description=desc)
    db.session.add(ach)

@quiz_bp.route('/achievements/<int:user_id>', methods=['GET'])
def get_achievements(user_id):
    achievements = Achievement.query.filter_by(user_id=user_id).all()
    
    # Calculate total points (sum of all quiz scores)
    total_score = db.session.query(db.func.sum(QuizScore.score)).filter(QuizScore.user_id==user_id).scalar() or 0
    
    return jsonify({
        "achievements": [{
            "name": a.name,
            "icon": a.icon,
            "description": a.description,
            "date": a.earned_at.strftime("%Y-%m-%d")
        } for a in achievements],
        "total_points": total_score
    })
