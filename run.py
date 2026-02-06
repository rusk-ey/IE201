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
import random
import json

@app.route("/interactive_table", methods=["GET", "POST"])
@login_required
def interactive_table():
    from table_generator import generate_table
    from genai_story_generator import generate_story

    # Hints and Story Logic – Already Working, No Changes Required
    column_hints = {
        "Int": "Interest Payment = Unpaid Balance × Annual Interest Rate",
        "PPmt": "Principal Payment = Loan Payment - Interest Payment",
        "UBA": "Unpaid Balance After Payment = Unpaid Balance - Principal Payment",
        "AO": "Amount Owed = Unpaid Balance + Interest Payment",
        "UIB": "Unpaid Interest Before Payment = Interest Payment (from previous year)",
        "UIA": "Unpaid Interest After Payment = Unpaid Interest Before Payment - Interest Payment",
    }
    AI_gen = False  # Flag for dynamic story generation
    import os
    JSON_FILE = os.path.join(os.path.dirname(__file__), "formatted_scenario_strings.json")

    def fetch_story_from_json(**kwargs):
        try:
            with open(JSON_FILE, "r") as f:
                stories = json.load(f)
                story_template = random.choice(stories)
                return story_template.format(**kwargs)
        except Exception as e:
            print(f"Error reading story from JSON: {e}")
            return "Error fetching story. Please ensure the JSON file is formatted correctly."

    if request.method == "POST":
        action = request.form.get("action")
        print(f"Action received: {action}")

        if action == "new_table":
            # Generate a new table and missing cell
            table, missing_cell, deferment_years = generate_table()

            session["table"] = table
            session["missing_cell"] = missing_cell
            session["story"] = None
            session["show_hint"] = False
            session["missing_column"] = missing_cell["Column"]

            # Generate or fetch a story
            try:
                initial_balance = table[0].get("UB", 0)
                interest_rate = (table[0]["Int"] / initial_balance * 100) if initial_balance else 0
                loan_payment = next((row.get("Ad", 0) for row in table if row.get("Ad", 0) > 0), 0)
                num_years = len(table)

                if AI_gen:
                    story_prompt = (
                        f"Write a short word problem about a business or person who borrows ${initial_balance:,.2f} "
                        f"at an annual interest rate of {interest_rate:.2f}%. Payments are deferred for {deferment_years} years before "
                        f"entering repayment. The repayment plan involves annual payments of ${loan_payment:,.2f} over the next "
                        f"{num_years - deferment_years} years."

                        "\n\n**Additional Requirements:**\n"
                        "- The word problem must use the following style and terminology as demonstrated in these examples:\n"
                        "    - A local startup, Horizon Tech, secures a business loan of ${initial_balance} to fund its initial operations. "
                        "The loan accrues interest at an annual rate of {interest_rate}%, and all payments are deferred for the first "
                        "{deferment_years} years. After this deferment period ends, the company enters a repayment schedule consisting of "
                        "fixed annual payments of ${loan_payment} for a term of {repayment_years} years.\n"
                        "    - A tech startup secures a loan of ${initial_balance} to cover initial research and development costs at an annual "
                        "interest rate of {interest_rate}%. Under the terms of the agreement, all payments are deferred for the first "
                        "{deferment_years} years. Following this deferral period, the startup enters a repayment phase requiring annual payments "
                        "of ${loan_payment} over a duration of {repayment_years} years.\n"
                        "    - A small tech startup secures a business loan of ${initial_balance} to fund the development of a new software platform. "
                        "The loan carries an annual interest rate of {interest_rate}%. According to the agreement, the company is granted a deferment "
                        "period of {deferment_years} years, during which no payments are required. Following the conclusion of this deferral period, "
                        "the startup enters a repayment phase consisting of fixed annual payments of ${loan_payment} for a duration of {repayment_years} years."
                        "\n- The word problem must strictly follow this vocabulary and tone, and avoid using any new or unapproved terminology beyond these examples."
                        "\n- Your response will be evaluated for compliance with these rules."
                    )

                    print(f"Generated Story Prompt: {story_prompt}")
                    story = generate_story(story_prompt)
                else:
                    story = fetch_story_from_json(
                        initial_balance=f"{initial_balance:,.2f}",
                        interest_rate=f"{interest_rate:.2f}",
                        deferment_years=str(deferment_years),
                        loan_payment=f"{loan_payment:,.2f}",
                        repayment_years=str(num_years - deferment_years),
                    )
                session["story"] = story
            except Exception as e:
                print(f"Error generating or fetching story: {e}")
                flash("Unable to generate story. Please try again.", "danger")

            flash("New table and word problem generated!", "info")
            return redirect(url_for("interactive_table"))

        elif action == "ask_question":
            # Handling student questions for Gemini
            try:
                user_question = request.form.get("custom_question", "").strip()
                if not user_question:
                    flash("Please enter a valid question!", "warning")
                    return redirect(url_for("interactive_table"))

                # Introduce PromptLevel variable
                PromptLevel = 1  # Default is detailed prompt, update this dynamically as needed (or user-configurable)

                # Retrieve context from session
                table = session.get("table", [])
                missing_cell = session.get("missing_cell", {})
                story = session.get("story", "No story available.")
                principal_amount = table[0].get("UB", "Unknown") if table else "Unknown"
                interest_rate = (
                    (table[0].get("Int", 0) / principal_amount * 100) if principal_amount else "Unknown"
                )
                total_loan_period = len(table)
                deferment_period = session.get("deferment_period", "Unknown")
                annual_payment = next((row.get("Ad", 0) for row in table if row.get("Ad", 0) > 0), "Unknown")

                # Build the table as part of the prompt
                table_prompt = ""
                for row in table[:5]:  # Limit rows for simplicity
                    table_prompt += (
                        f"| {row['Year']} | "
                        f"{'BLANK' if row['UB'] is None else row['UB']} | "
                        f"{'BLANK' if row['Int'] is None else row['Int']} | "
                        f"{'BLANK' if row['UIB'] is None else row['UIB']} | "
                        f"{row['AO']} | {row['Ad']} | "
                        f"{'BLANK' if row['IPmt'] is None else row['IPmt']} | "
                        f"{'BLANK' if row['PPmt'] is None else row['PPmt']} | "
                        f"{row['UIA']} | {row['UBA']} |\n"
                    )

                # Generate detailed or simple prompts based on PromptLevel
                if PromptLevel == 1:
                    # Detailed prompt (PromptLevel = 1)
                    prompt = f"""
                    You are a chatbot embedded within an interactive educational tool designed to help undergraduate students in a financial engineering course (Engineering Economy). 

                    **Scenario Context:**
                    This tool is used to teach students about loan repayment, interest, including Unpaid Balance (UB), Interest Payment (Int), Principal Payment (PPmt), and other finance-related topics. 
                    Always ensure the vocabulary and terminology in your responses exactly match the wording used in the provided story question below.

                    **Rules for Answering Questions:**
                    - Do not fully calculate the solution for any blank. Instead, guide the student by providing:
                        - The correct formula or equations.
                        - Definitions of variables as they relate to the table and story prompt.
                        - General financial principles and reasoning.
                        - Example calculations from other rows in the table to demonstrate general methods applicable to their blank value.
                        - Hints to help the user figure out the problem for themselves.
                    - Do NOT reveal the solution to any blank cell directly in your response.

                    **Word Problem Context**:
                    {story}

                    **Relevant Loan Details:**
                    - Principal Loan Amount: {principal_amount} USD
                    - Annual Interest Rate: {interest_rate}%
                    - Total Loan Period: {total_loan_period} years
                    - Deferment Period: {deferment_period} years
                    - Loan Repayment Amount Per Year (after deferment): {annual_payment} USD

                    **Loan Table (Partial View)**:
                    Below is the loan table generated for this question. Use this table to provide context for your answer. If a value is missing, it is represented as `BLANK`.

                    | Year | UB (Unpaid Balance) | Int (Interest Payment) | UIB (Unpaid Interest Before Payment) | AO (Amount Owed) | Ad (Loan Payment) | IPmt (Interest Payment) | PPmt (Principal Payment) | UIA (Unpaid Interest After Payment) | UBA (Unpaid Balance After Payment) |
                    |------|---------------------|------------------------|---------------------------------------|------------------|-------------------|--------------------------|---------------------------|--------------------------------------|------------------------------------|
                    {table_prompt}

                    **Student Question**:
                    "{user_question}"

                    **Specific Blank Context**:
                    The student is focused on calculating the value for the `{missing_cell.get('Column', 'Unknown')}` in year `{missing_cell.get('Year', 'Unknown')}`.

                    **Instructions for Answering**:
                    - Your role is to guide students in understanding the concepts, not to provide full numerical answers to their specific problem.
                    - Try to provide concrete tips, insights, or partial steps to help the student learn how to solve the problem on their own.
                    - Avoid introducing new terminology or format conventions. Stick to the vocabulary and phrasing used in the word problem.
                    - If applicable, use other rows from the table as examples to demonstrate principles or calculations.
            - Always write math descriptions and equations in plain text instead of using LaTeX. For example:
              - Write `A = B * C` instead of `$A = B \\times C$`.
              - Include simple plain English descriptions where necessary.
            

                    Always focus your response on being concise, helpful, and relevant to THIS specific problem.
                    """
                else:
                    # Simple prompt (PromptLevel = 0)
                    prompt = f"The student has asked the following question:\n\n{user_question}\n\nPlease provide a concise and clear explanation to help the student understand the concept."

                # Logging the prompt (for debugging purposes)
                print(f"Generated Gemini Prompt:\n{prompt}")

                # Send prompt to Gemini and capture the response (mocked here)
                gemini_response = generate_story(prompt)  # Replace with actual Gemini API call

                # Convert Markdown response into HTML for frontend rendering
                from markdown import markdown
                gemini_response_html = markdown(gemini_response)

                # Store the rendered response into the session
                session["gemini_answer"] = gemini_response_html
                flash("Gemini has answered your question!", "success")
            except Exception as e:
                print(f"Error while submitting question to Gemini: {e}")
                flash("An error occurred while processing your question. Please try again.", "danger")

            return redirect(url_for("interactive_table"))

        elif action == "validate":
            try:
                user_input = float(request.form.get("user_input"))
                missing_year = int(request.form.get("missing_year"))
                missing_column = request.form.get("missing_column")

                table = session.get("table")
                missing_cell = session.get("missing_cell")
                if not table or not missing_cell:
                    flash("Error: Missing session data. Please generate a new table.", "danger")
                    return redirect(url_for("interactive_table"))

                if missing_cell["Year"] == missing_year and missing_cell["Column"] == missing_column:
                    correct_value = missing_cell["CorrectValue"]
                    tolerance = 10
                    if abs(user_input - correct_value) <= tolerance:
                        flash("Correct! Great job!", "success")
                        session["show_hint"] = False

                        # Generate new table for next question
                        table, missing_cell, deferment_years = generate_table()
                        session["table"] = table
                        session["missing_cell"] = missing_cell
                        session["story"] = None
                        return redirect(url_for("interactive_table"))
                    else:
                        flash("Incorrect! Try again.", "danger")
                        session["show_hint"] = True

                return redirect(url_for("interactive_table"))

            except Exception as e:
                print(f"Error during validation: {e}")
                flash("Validation failed. Please try again.", "danger")
                return redirect(url_for("interactive_table"))

    table = session.get("table")
    missing_cell = session.get("missing_cell")
    story = session.get("story")
    show_hint = session.get("show_hint", False)
    missing_column = session.get("missing_column", None)
    hint = column_hints.get(missing_column, None) if show_hint and missing_column else None

    return render_template(
        "interactive_table.html",
        table=table,
        missing_cell=missing_cell,
        story=story,
        show_hint=show_hint,
        hint=hint,
        gemini_answer=session.get("gemini_answer")  # Pass Gemini answer if available
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