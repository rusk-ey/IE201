from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import db, StudentProgress, generate_problem, check_answer


main = Blueprint('main', __name__)

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/practice", methods=["GET", "POST"])
def practice():
    if request.method == "POST":
        student_id = 1  # Dummy student ID for now
        problem_type = request.form.get("problem_type", "addition")
        answer = request.form.get("answer")
        correct_answer = float(request.form.get("correct_answer"))  # Convert to float for division

        # Determine correctness and flash feedback
        if answer:
            if check_answer(answer, correct_answer):
                flash("Correct! Great job!", "success")
                solution = f"The correct answer was {correct_answer}. Well done!"
            else:
                flash("Incorrect. Keep trying!", "danger")
                solution = f"The correct answer was {correct_answer}. Don't worry, you'll get it next time!"
        else:
            flash("Please select an answer.", "warning")
            solution = ""

        # Update progress in the database
        StudentProgress.update_progress(student_id, problem_type, answer and float(answer) == correct_answer)

        problem = generate_problem()  # Generate a new problem
        return render_template("question.html", problem=problem, solution=solution)

    # Generate a random problem on GET requests
    problem = generate_problem()
    return render_template("question.html", problem=problem, solution=None)

@main.route("/progress")
def progress():
    student_id = 1  # Dummy student ID for now
    progress = StudentProgress.get_progress(student_id)
    return render_template("progress.html", progress=progress)