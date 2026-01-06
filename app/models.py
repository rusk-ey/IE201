from flask_sqlalchemy import SQLAlchemy
import random

db = SQLAlchemy()

class StudentProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    problem_type = db.Column(db.String(20), nullable=False)
    correct_count = db.Column(db.Integer, default=0, nullable=False)  # Default to 0
    attempt_count = db.Column(db.Integer, default=0, nullable=False)  # Default to 0

    @classmethod
    def update_progress(cls, student_id, problem_type, is_correct):
        progress = cls.query.filter_by(student_id=student_id, problem_type=problem_type).first()
        if not progress:
            progress = cls(student_id=student_id, problem_type=problem_type, correct_count=0, attempt_count=0)
            db.session.add(progress)

        progress.attempt_count += 1
        if is_correct:
            progress.correct_count += 1

        db.session.commit()

    @classmethod
    def get_progress(cls, student_id):
        return cls.query.filter_by(student_id=student_id).all()

def generate_problem():
    problem_type = random.choice(['addition', 'subtraction', 'multiplication', 'division'])
    num1, num2 = random.randint(1, 20), random.randint(1, 20)

    if problem_type == "addition":
        correct_answer = num1 + num2
    elif problem_type == "subtraction":
        correct_answer = num1 - num2
    elif problem_type == "multiplication":
        correct_answer = num1 * num2
    elif problem_type == "division":
        num1 = num1 * num2  # Ensure num1 is divisible by num2 for simplicity
        correct_answer = num1 / num2

    options = [correct_answer] + random.sample(range(1, 100), 3)
    random.shuffle(options)

    return {
        "question": f"{num1} {'+' if problem_type == 'addition' else '-' if problem_type == 'subtraction' else '*' if problem_type == 'multiplication' else '/'} {num2}",
        "correct_answer": correct_answer,
        "options": options,
        "problem_type": problem_type
    }

def check_answer(answer, correct_answer):
    return float(answer) == float(correct_answer)

def initialize_database(app):
    with app.app_context():
        db.create_all()