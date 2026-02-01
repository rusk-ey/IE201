from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
import random
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("Agg")  # Use the Agg backend for matplotlib
from io import BytesIO
import base64
from gen_q import *
import os

print("Current Working Directory:", os.getcwd())

# Initialize Flask app
app = Flask(__name__, template_folder="app/templates")
app.secret_key = "super-secret-key"

# Configure the database
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
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password. Please try again.", "danger")
    return render_template('login.html', form=form)

@app.route("/practice", methods=["GET", "POST"])
@login_required
def practice():
    """Render practice problems (arithmetic or cash flow)."""

    # Handle submission (POST request)
    if request.method == "POST":
        # Retrieve submitted answer and problem details
        user_answer = float(request.form.get("answer"))
        correct_answer = float(request.form.get("correct_answer"))
        problem_type = request.form.get("problem_type")

        # Record user progress in the database
        progress_entry = Progress.query.filter_by(user_id=current_user.id, problem_type=problem_type).first()
        if not progress_entry:
            progress_entry = Progress(user_id=current_user.id, problem_type=problem_type, correct_count=0, attempt_count=0)
            db.session.add(progress_entry)

        # Update progress counts
        progress_entry.attempt_count += 1
        if user_answer == correct_answer:
            progress_entry.correct_count += 1
            flash("Correct! Well done!", "success")
        else:
            flash(f"Incorrect! The correct answer was ${correct_answer:.2f}.", "danger")

        # Commit changes to progress and reload for the next question
        db.session.commit()
        return redirect(url_for("practice"))  # Redirect to a new question

    # Handle fresh question generation (GET request)
    else:
        problem = generate_problem()  # Ensure a new problem is always generated

        if problem["type"] in ["Irregular", "Uniform", "Gradient"]:
            # Render cash flow problems
            return render_template("question.html", problem=problem)
        else:
            # Generate plot for arithmetic problems
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

from flask import session

@app.route("/interactive_table", methods=["GET", "POST"])
@login_required
def interactive_table():
    from table_generator import generate_table
    from genai_story_generator import generate_story

    # Define hints mapping for each column
    column_hints = {
        "Int": "Interest Payment = Unpaid Balance × Annual Interest Rate",
        "PPmt": "Principal Payment = Loan Payment - Interest Payment",
        "UBA": "Unpaid Balance After Payment = Unpaid Balance - Principal Payment",
        "AO": "Amount Owed = Unpaid Balance + Interest Payment",
        "UIB": "Unpaid Interest Before Payment = Interest Payment (from previous year)",
        "UIA": "Unpaid Interest After Payment = Unpaid Interest Before Payment - Interest Payment",
    }

    if request.method == "POST":
        action = request.form.get("action")
        print(f"Action received: {action}")  # Debugging

        if action == "new_table":
            table, missing_cell, deferment_years = generate_table()

            # Update session variables with new table and clear hint
            session["table"] = table
            session["missing_cell"] = missing_cell
            session["story"] = None  # Clear the story if a new table is generated
            session["show_hint"] = False  # Reset hint visibility
            session["missing_column"] = missing_cell["Column"]  # Set the column being tested

            # Generate story (retaining existing logic)
            try:
                initial_balance = table[0].get("UB", 0)
                interest_rate = (table[0]["Int"] / initial_balance * 100) if initial_balance else 0
                loan_payment = next((row.get("Ad", 0) for row in table if row.get("Ad", 0) > 0), 0)
                num_years = len(table)

                story_prompt = (
                    f"Write a short word problem about a business or person who borrows ${initial_balance:,.2f} at an annual interest "
                    f"rate of {interest_rate:.2f}%. Payments are deferred for {deferment_years} years before entering repayment. "
                    f"The repayment plan involves annual payments of ${loan_payment:,.2f} over the next {num_years - deferment_years} years. "
                    f"Describe the loan, deferral period, deferral years, and repayment terms without including explanations or solutions."
                )
                print(f"Generated Story Prompt: {story_prompt}")

                story = generate_story(story_prompt)
                session["story"] = story
            except Exception as e:
                print(f"Error while generating new table: {e}")
                flash("An error occurred during table creation. Please try again.", "danger")

            flash("New table and word problem generated!", "info")
            return redirect(url_for("interactive_table"))

        elif action == "validate":
            try:
                # Retrieve form inputs
                user_input = float(request.form.get("user_input"))
                missing_year = int(request.form.get("missing_year"))
                missing_column = request.form.get("missing_column")

                # Retrieve table and missing cell info from session
                table = session.get("table")
                missing_cell = session.get("missing_cell")
                if not table or not missing_cell:
                    flash("Error: Missing session data. Please generate a new table.", "danger")
                    return redirect(url_for("interactive_table"))

                # Find correct value for validation
                if missing_cell["Year"] == missing_year and missing_cell["Column"] == missing_column:
                    correct_value = missing_cell["CorrectValue"]
                    tolerance = 10  # Use existing validation tolerance
                    if abs(user_input - correct_value) <= tolerance:
                        flash("Correct! Well done!", "success")
                        session["show_hint"] = False  # Hide hint upon correct answer
                        session["missing_column"] = None  # Reset column test tracking

                        # Generate a new table for the next question
                        table, missing_cell, deferment_years = generate_table()
                        session["table"] = table
                        session["missing_cell"] = missing_cell
                        session["story"] = None
                        return redirect(url_for("interactive_table"))
                    else:
                        flash(f"Incorrect! Try again. See hints for guidance.", "danger")
                        session["show_hint"] = True  # Show hint upon incorrect answer

                # Reload the same problem for retries
                return redirect(url_for("interactive_table"))

            except Exception as e:
                print(f"Error during validation: {e}")
                flash("An error occurred while validating your answer. Please try again.", "danger")
                return redirect(url_for("interactive_table"))

    # Handle GET requests (render the page based on session data)
    table = session.get("table")
    missing_cell = session.get("missing_cell")
    story = session.get("story")
    show_hint = session.get("show_hint", False)

    # Generate initial data if missing
    if not table or not missing_cell or not story:
        table, missing_cell, deferment_years = generate_table()
        session["table"] = table
        session["missing_cell"] = missing_cell
        session["missing_column"] = None
        session["show_hint"] = False

        try:
            initial_balance = table[0].get("UB", 0)
            interest_rate = (table[0]["Int"] / initial_balance * 100) if initial_balance else 0
            loan_payment = next((row.get("Ad", 0) for row in table if row.get("Ad", 0) > 0), 0)
            num_years = len(table)

            story_prompt = (
                f"Write a short word problem about a business or person who borrows ${initial_balance:,.2f} at an annual interest "
                f"rate of {interest_rate:.2f}%. Payments are deferred for {deferment_years} years before entering repayment. "
                f"The repayment plan involves annual payments of ${loan_payment:,.2f} over the next {num_years - deferment_years} years. "
                f"Describe the loan, deferral period, deferral years, and repayment terms without including explanations or solutions."
            )

            print(f"Generated Story Prompt: {story_prompt}")
            story = generate_story(story_prompt)
            session["story"] = story
        except Exception as e:
            print(f"Error processing story during GET: {e}")
            flash("Unable to generate the story. Please try again!", "danger")

    # Add column-specific hints if a question is active
    missing_column = session.get("missing_column", None)
    hint = column_hints.get(missing_column, None) if show_hint and missing_column else None

    return render_template(
        "interactive_table.html",
        table=table,
        missing_cell=missing_cell,
        story=story,
        show_hint=show_hint,
        hint=hint  # Pass hint to the template
    )

def generate_problem():
    # Get user progress to calculate correctness percentages
    user_progress = Progress.query.filter_by(user_id=current_user.id).all()

    # Calculate correctness percentages (correct_count / attempt_count)
    response_percentages = {}
    for entry in user_progress:
        if entry.attempt_count > 0:
            response_percentages[entry.problem_type] = entry.correct_count / entry.attempt_count
        else:
            response_percentages[entry.problem_type] = 0.0

    # Generate a random problem
    problem = Problem()
    problem.get_type(response_percentages)  # Adjusting type selection adaptively
    problem.get_problem()

    # Chart cash flows using matplotlib
    plot = generate_cash_flow_chart(problem.cash_flows, problem.type, problem.i, problem.n, problem.sol)

    # Multiple-choice options
    correct_answer = round(problem.sol, 2)  # Round to 2 decimal places
    options = {correct_answer}
    while len(options) < 4:
        options.add(round(correct_answer + random.uniform(-1000, 1000), 2))  # Ensure 4 unique options
    options = list(options)
    random.shuffle(options)

    return {
        "type": problem.type,
        "i": problem.i,
        "n": problem.n,
        "cash_flows": problem.cash_flows,
        "correct_answer": correct_answer,
        "options": options,
        "plot": plot,
    }

def generate_cash_flow_chart(cash_flows, problem_type, interest_rate, periods, solution):
    fig, ax = plt.subplots(figsize=(10, 4))

    # Plot cash flows as vertical bars
    periods = list(cash_flows.keys())
    flows = list(cash_flows.values())
    ax.bar(periods, flows, width=0.3, color="blue", zorder=3)

    # Dynamically set the Y-axis limit based on the highest cash flow
    max_flow = max(flows) if flows else 0  # Safeguard against empty cash flows
    ax.set_ylim(0, max_flow * 1.4)  # Add a buffer of 40% above the highest bar

    # Add labels for each cash flow
    for i, flow in enumerate(flows):
        ax.text(
            i,  # X position (center of each bar)
            flow + (max_flow * 0.05),  # Slightly above each cash flow bar
            f"${flow:,}",  # Format with comma separator
            ha="center", va="bottom", fontsize=9  # Text styling
        )

    # Chart details
    ax.set_title(f"Cash Flow Diagram (i={interest_rate * 100:.2f}%)", fontsize=14, pad=20)
    ax.set_xlabel("Periods (n)", fontsize=12)
    ax.set_ylabel("Cash Flow Amount", fontsize=12)
    ax.axhline(0, color="black", linewidth=1.3)
    ax.grid(True, linestyle="--", alpha=0.7)

    # Convert plot to PNG for use in the template
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    encoded_image = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    plt.close(fig)
    return encoded_image

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