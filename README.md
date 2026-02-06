# IE201 Learning Tool - Interactive Loan repayment Practice

An interactive educational web application designed to help undergraduate students in financial engineering (Engineering Economy) learn loan repayment concepts through practice problems with AI-powered assistance.

## Project Overview

This tool generates loan repayment tables with one missing value that students must calculate. Students receive word problems describing realistic loan scenarios and can ask questions to an AI assistant (Gemini) that provides guidance without directly solving the problem.

---

## Key Files and Their Relationships

### Core Application Files

#### **1. `run.py`**
The main Flask application that serves the web interface.

**Key Components:**
- **Route: `/interactive_table`** - Main application route that handles:
  - Generating new tables and word problems
  - Validating student answers
  - Processing AI assistant questions
- **Imports:** `table_generator.py`, `genai_story_generator.py`
- **Templates:** Renders `interactive_table.html`
- **Session Management:** Stores table data, missing cell information, stories, and hints

- 
---

#### **2. `table_generator.py`**
Generates realistic loan repayment tables with financial calculations.

**Key Functions:**
- `generate_table()` - Creates a loan table with:
  - Random loan parameters (balance, interest rate, deferment period)
  - Calculated values for all cells (UB, Int, UIB, AO, Ad, IPmt, PPmt, UIA, UBA)
  - One randomly selected blank cell for the student to fill
  
**Returns:**
- `table`: List of dictionaries representing each year's financial data
- `missing_cell`: Dictionary with Year, Column, and CorrectValue of the blank
- `deferment_years`: Number of years payments are deferred

**Used by:** `run.py`, evaluation scripts

---

#### **3. `genai_story_generator.py`**
Generates word problems (stories) that describe loan scenarios using AI.

**Key Functions:**
- `generate_story(prompt)` - Calls the Gemini API to create contextual word problems

**Constraints:**
- Must use approved terminology from `formatted_scenario_strings.json`
- Avoids technical jargon like "repayment"
- Describes loan terms, deferment period, and repayment schedule

**Used by:** `run.py`, evaluation scripts

---

### Frontend Files

#### **4. `templates/interactive_table.html`**
The main user interface for the interactive practice tool.

**Features:**
- Displays the loan repayment table with one blank cell (input field)
- Shows the word problem describing the loan scenario
- Provides a form to submit answers for validation
- "Generate New Table" button for new practice problems
- "Ask a Question" section for AI-powered assistance
- Displays hints when answers are incorrect
- Renders AI responses (with Markdown support)

**Extends:** `base.html`

**Dynamic Content:**
- `{{ table }}` - The loan table data
- `{{ missing_cell }}` - Information about the blank cell
- `{{ story }}` - The word problem
- `{{ hint }}` - Formula hint (shown after incorrect answer)
- `{{ gemini_answer }}` - AI assistant's response

---

#### **5. `templates/base.html`**
Base template that provides the common layout, styling, and navigation.

**Provides:**
- Bootstrap CSS framework
- Common navigation header
- Flash message handling
- Page structure that child templates extend

---

### Data and Configuration Files

#### **6. `formatted_scenario_strings.json`**
Contains approved example word problems that define acceptable terminology.

**Purpose:**
- Ensures consistency in language across generated stories
- Defines approved vocabulary (e.g., "deferred," "repayment phase," "annual payments")
- Used to evaluate whether AI responses use appropriate terminology

### Evaluation and Testing Files

#### **7. `gemini_evaluation.py`**
Automated testing and evaluation script that assesses the quality and compliance of AI assistant responses.

**Purpose:**
- Validates that Gemini's responses adhere to educational guidelines
- Ensures responses use only approved terminology
- Checks that responses guide students without directly solving problems
- Provides quantitative metrics (1-10 scores) and qualitative feedback

**Workflow:**

1. **Test Case Generation** (`generate_test_cases(num_cases, prompt_level)`):
   - Generates `num_cases` (default: 50) unique test scenarios
   - Each test case includes:
     - A randomly generated loan table with one blank cell (via `table_generator.py`)
     - A contextual word problem (via `genai_story_generator.py`)
     - A dummy student question: `"How do I calculate the [Column] for Year [X]?"`
     - A detailed or simple prompt based on `prompt_level`
     - A Gemini-generated response to the prompt

2. **Prompt Level Configuration**:
   - **Level 0 (Simple):** Sends only the student question with minimal context
   - **Level 1 (Detailed):** Includes full context:
     - Educational rules and guidelines
     - Complete word problem and loan details
     - Partial table view (first 5 rows)
     - Specific blank cell context
     - Instructions to avoid direct solutions
   - **Level 2 (Medium):** Includes context but fewer instructional rules

3. **Response Evaluation** (`evaluate_responses_with_openai(approved_examples, test_cases)`):
   - Loads approved terminology from `formatted_scenario_strings.json`
   - For each test case:
     - Constructs an evaluation prompt that includes:
       - The original question and context
       - Gemini's response
       - Evaluation rules and criteria
       - List of approved examples
     - Sends the evaluation prompt to OpenAI's GPT-4 API
     - Receives a score (1-10) and detailed feedback

**Evaluation Criteria:**
- ✅ **Terminology Compliance:** Uses only vocabulary from approved examples
- ✅ **No Direct Solutions:** Provides guidance without solving the blank cell
- ✅ **Helpful Guidance:** Includes formulas, hints, and example calculations
- ✅ **Clarity:** Clear language matching the word problem's vocabulary
- ❌ **Forbidden Terms:** Penalizes use of terms like "amortization" (score ≤ 2)
- ❌ **Direct Answers:** Penalizes revealing the solution (score ≤ 2)

**Key Functions:**

```python
# Generate 50 test cases with detailed prompts (Level 1)
test_cases = generate_test_cases(num_cases=50, prompt_level=1)

# Load approved terminology examples
approved_examples = load_approved_examples("formatted_scenario_strings.json")

# Evaluate all responses using OpenAI
results = evaluate_responses_with_openai(approved_examples, test_cases)

# Save results to JSON file
with open("gemini_evaluation_results1_1.json", "w") as f:
    json.dump(results, f, indent=4)

IE201/
├── run.py                          # Main Flask application
├── table_generator.py              # Loan table generation logic
├── genai_story_generator.py        # AI story generation
├── gemini_evaluation_results.py    # Evaluation script
├── formatted_scenario_strings.json # Approved terminology examples
├── requirements.txt                # Python dependencies
├── .env                            # API keys (not in Git)
├── .gitignore                      # Git exclusions
├── templates/
│   ├── base.html                   # Base template
│   └── interactive_table.html      # Main UI
└── static/                         # CSS, JS, images (if any)

