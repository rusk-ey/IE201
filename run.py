from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
import random
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
import sqlite3

print("Current Working Directory:", os.getcwd())

with open("test_file.txt", "w") as f:
    f.write("This is a test.")
print("Test file written successfully!")

# Initialize Flask app
app = Flask(__name__, template_folder="app/templates")
app.secret_key = "super-secret-key"

# Configure the database
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ie201.db'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

import os

if os.environ.get("DATABASE_URL"):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL'].replace("postgres://", "postgresql://", 1)
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///ie201.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"  # Redirect unauthenticated users to the login page


# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)


class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"))
    problem_type = db.Column(db.String(50), nullable=False)
    correct_count = db.Column(db.Integer, default=0)
    attempt_count = db.Column(db.Integer, default=0)


# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Forms
class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=6)])
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user = User.query.filter_by(username=username.data).first()
        if existing_user:
            raise ValidationError("This username is already taken. Please choose another.")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=6)])
    submit = SubmitField("Login")


# Routes
@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Your account has been created! Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash("You are now logged in!", "success")
            return redirect(url_for('practice'))
        else:
            flash("Invalid username or password. Please try again.", "danger")
    return render_template('login.html', form=form)



@app.route("/practice", methods=["GET", "POST"])
@login_required
def practice():
    """Render math problem with a number line plot."""
    problem = generate_problem()
    plot = None  # In case of a GET request, no image is initially shown

    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = float(request.form.get("correct_answer"))
        problem_type = request.form.get("problem_type")

        # Update progress in the database for the logged-in user
        progress_entry = Progress.query.filter_by(user_id=current_user.id, problem_type=problem_type).first()
        if not progress_entry:
            progress_entry = Progress(user_id=current_user.id, problem_type=problem_type, correct_count=0,
                                      attempt_count=0)
            db.session.add(progress_entry)

        # Update progress counts
        progress_entry.attempt_count += 1
        if user_answer and float(user_answer) == correct_answer:
            progress_entry.correct_count += 1
            flash("Correct! Well done!", "success")
        else:
            flash(f"Incorrect! The correct answer was {correct_answer}.", "error")

        db.session.commit()
        return redirect(url_for("practice"))

    # Generate a plot for the current problem
    plot = generate_number_line(problem["num1"], problem["num2"], problem["operation"])

    return render_template("question.html", problem=problem, plot=plot)


@app.route("/progress")
@login_required
def progress():
    user_progress = Progress.query.filter_by(user_id=current_user.id).all()
    progress_data = [
        {"problem_type": entry.problem_type, "correct_count": entry.correct_count, "attempt_count": entry.attempt_count}
        for entry in user_progress
    ]
    return render_template("progress.html", progress=progress_data)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


# Utility functions for generating problems and plots
def generate_problem():
    operations = {
        "+": "Addition",
        "-": "Subtraction",
        "*": "Multiplication",
        "/": "Division"
    }

    num1 = random.randint(1, 20)
    num2 = random.randint(1, 20)
    operation = random.choice(list(operations.keys()))

    if operation == "/":
        while num2 == 0 or num1 % num2 != 0:
            num1 = random.randint(1, 20)
            num2 = random.randint(1, 20)
        correct_answer = round(num1 / num2, 2)
        question = f"What is {num1} ÷ {num2}?"
    else:
        question = f"What is {num1} {operation} {num2}?"
        correct_answer = eval(f"{num1} {operation} {num2}")

    options = set()
    while len(options) < 3:
        lower_bound = int(correct_answer - 5)
        upper_bound = int(correct_answer + 5)
        options.add(random.randint(lower_bound, upper_bound))
    options.add(correct_answer)

    return {
        "question": question,
        "correct_answer": correct_answer,
        "problem_type": operations[operation],
        "num1": num1,
        "num2": num2,
        "operation": operation,
        "options": list(options)
    }


def generate_number_line(num1, num2, operation):
    result = None
    if operation == "+":
        result = num1 + num2
    elif operation == "-":
        result = num1 - num2
    elif operation == "*":
        result = num1 * num2
    elif operation == "/":
        result = round(num1 / num2, 2)

    fig, ax = plt.subplots(figsize=(6, 2))
    ax.hlines(0, -10, max(num1, num2, result) + 5, color='black')
    ax.scatter([num1, num2, result], [0, 0, 0], color=['blue', 'orange', 'green'], zorder=3)
    ax.text(num1, 0.2, f"{num1}", fontsize=10, ha='center')
    ax.text(num2, 0.2, f"{num2}", fontsize=10, ha='center')
    ax.text(result, 0.2, f"{result}", fontsize=10, ha='center')
    ax.set_ylim(-1, 1)
    ax.get_yaxis().set_visible(False)
    ax.get_xaxis().tick_bottom()

    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    encoded_plot = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    return encoded_plot


# Run the application
if __name__ == "__main__":
    with app.app_context():
        print("Running db.create_all() to initialize the database...")
        db.create_all()  # Create the tables in the database
        print("Database tables creation is complete!")
    app.run(debug=True)

with open("test_file.txt", "w") as f:
    f.write("This is a test.")

import os
import sqlite3
import os
import sqlite3

# Verify the database file exists
db_path = "ie201.db"
if not os.path.exists(db_path):
    print(f"Database file '{db_path}' does not exist!")
else:
    print(f"Database file found at: {os.path.abspath(db_path)}")

# Proceed with SQLite connection
connection = sqlite3.connect(db_path)

import sqlite3

# Connect to your database
connection = sqlite3.connect("ie201.db")

# Create a cursor object to execute SQL commands
cursor = connection.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in the database:")
for table in tables:
    print(table[0])

# Check the schema of the `user` table
cursor.execute("PRAGMA table_info(user);")
print("\nSchema of the 'user' table:")
for column in cursor.fetchall():
    print(column)

# Check the schema of the `progress` table
cursor.execute("PRAGMA table_info(progress);")
print("\nSchema of the 'progress' table:")
for column in cursor.fetchall():
    print(column)

# Close the connection
connection.close()