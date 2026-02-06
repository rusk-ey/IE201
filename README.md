# IE201 Learning Tool - Interactive Loan Amortization Practice

An interactive educational web application designed to help undergraduate students in financial engineering (Engineering Economy) learn loan amortization concepts through practice problems with AI-powered assistance.

## Project Overview

This tool generates loan amortization tables with one missing value that students must calculate. Students receive word problems describing realistic loan scenarios and can ask questions to an AI assistant (Gemini) that provides guidance without directly solving the problem.

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
Generates realistic loan amortization tables with financial calculations.

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
- Avoids technical jargon like "amortization"
- Describes loan terms, deferment period, and repayment schedule

**Used by:** `run.py`, evaluation scripts

---

### Frontend Files

#### **4. `templates/interactive_table.html`**
The main user interface for the interactive practice tool.

**Features:**
- Displays the loan amortization table with one blank cell (input field)
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

**Format:**
```json
[
    "A local startup, Horizon Tech, secures a business loan of ${initial_balance}...",
    "A tech startup secures a loan of ${initial_balance}...",
    ...
]

