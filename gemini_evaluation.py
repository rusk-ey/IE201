import random
from markdown import markdown
from openai import OpenAI
import json
import os

# Import the table generator function
from table_generator import generate_table
from genai_story_generator import generate_story

### CONFIGURE OPENAI API KEY ###

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise Exception("OPENAI_API_KEY environment variable is missing. Please set it before running the script.")

client = OpenAI(api_key=API_KEY)  # Replace hardcoded key
client = OpenAI(api_key=API_KEY)  # uses API key from code or env, same as before

# Function to generate 50 test cases with user questions and prompts based on PromptLevel
def generate_test_cases(num_cases=50, prompt_level=1, approved_examples=[]):
    """
    Generate test cases with dummy user inputs, tables, and prompts.
    :param num_cases: Number of test cases to generate.
    :param prompt_level: The level of detail for the prompt (1 = detailed, 0 = simple).
    :return: A list of test cases, each containing table, story, question, prompt, and response.
    """
    test_cases = []

    example_str = "\n".join([f"{i + 1}. {example}" for i, example in enumerate(approved_examples)])

    for i in range(num_cases):
        # Generate table, missing cell, and story
        table, missing_cell, deferment_years = generate_table()


        # Generate dummy user question
        question = f"How do I calculate the {missing_cell['Column']} for Year {missing_cell['Year']}?"

        # Generate detailed or simple prompt
        principal_amount = table[0].get("UB", "Unknown")
        interest_rate = (
            (table[0].get("Int", 0) / principal_amount * 100) if principal_amount else "Unknown"
        )
        total_loan_period = len(table)
        annual_payment = next((row.get("Ad", 0) for row in table if row.get("Ad", 0) > 0), "Unknown")

        # Build table section in Markdown
        table_prompt = ""
        for row in table[:5]:  # Display only first 5 rows for prompt
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
        initial_balance = table[0].get("UB", 0)
        interest_rate = (table[0]["Int"] / initial_balance * 100) if initial_balance else 0
        loan_payment = next((row.get("Ad", 0) for row in table if row.get("Ad", 0) > 0), 0)
        num_years = len(table)

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

        story = generate_story(story_prompt)

        # Construct prompt based on PromptLevel

        if prompt_level == 1:
            prompt = f"""
            You are a chatbot embedded within an interactive educational tool designed to help undergraduate students in a financial engineering course (Engineering Economy). 

            **Scenario Context:**
            This tool is used to teach students about loan repayment concepts, including Unpaid Balance (UB), Interest Payment (Int), Principal Payment (PPmt), and other finance-related topics. 
            Always ensure the vocabulary and terminology in your responses exactly match the wording used in the provided story question below.

            **Rules for Answering Questions:**
            - Do not fully calculate the solution for any blank. Instead, guide the student by providing:
                - The correct formula or equations.
                - Definitions of variables as they relate to the table and story prompt.
                - General financial principles and reasoning.
                - Example calculations from other rows in the table to demonstrate general methods applicable to their blank value.
                - Hints to help the user figure out the problem for themselves.
            - Do NOT reveal the solution to any blank cell directly in your response.
            - The response must not include terminology or phrasing for describing financial engineering concepts outside the provided set of approved examples. Be strict and harsh about this. An example of this would be using the term 'amortization', which does not appear in the approved examples.
            - The approved examples are:
            {example_str}

            **Word Problem Context**:
            {story}

            **Relevant Loan Details:**
            - Principal Loan Amount: {principal_amount} USD
            - Annual Interest Rate: {interest_rate}%
            - Total Loan Period: {total_loan_period} years
            - Deferment Period: {deferment_years} years
            - Loan Repayment Amount Per Year (after deferment): {annual_payment} USD

            **Loan Table (Partial View)**:
            Below is the loan table generated for this question. Use this table to provide context for your answer. If a value is missing, it is represented as `BLANK`.

            | Year | UB (Unpaid Balance) | Int (Interest Payment) | UIB (Unpaid Interest Before Payment) | AO (Amount Owed) | Ad (Loan Payment) | IPmt (Interest Payment) | PPmt (Principal Payment) | UIA (Unpaid Interest After Payment) | UBA (Unpaid Balance After Payment) |
            |------|---------------------|------------------------|---------------------------------------|------------------|-------------------|--------------------------|---------------------------|--------------------------------------|------------------------------------|
            {table_prompt}

            **Student Question**:
            "{question}"

            **Specific Blank Context**:
            The student is tasked with calculating the value for the `{missing_cell.get('Column', 'Unknown')}` in year `{missing_cell.get('Year', 'Unknown')}`.

            **Instructions for Answering**:
            - Your role is to guide students in understanding the concepts, not to provide full numerical answers to their specific problem.
            - Try to provide concrete tips, insights, or partial steps to help the student learn how to solve the problem on their own.
            - Avoid introducing new terminology or format conventions. Stick to the vocabulary and phrasing used in the word problem.
            - If applicable, use other rows from the table as examples to demonstrate principles or calculations.
            """
        elif prompt_level == 2:
            prompt = f"""
                        **Word Problem Context**:
                        {story}

                        **Relevant Loan Details:**
                        - Principal Loan Amount: {principal_amount} USD
                        - Annual Interest Rate: {interest_rate}%
                        - Total Loan Period: {total_loan_period} years
                        - Deferment Period: {deferment_years} years
                        - Loan Repayment Amount Per Year (after deferment): {annual_payment} USD

                        **Loan Table (Partial View)**:
                        Below is the loan table generated for this question. Use this table to provide context for your answer. If a value is missing, it is represented as `BLANK`.

                        | Year | UB (Unpaid Balance) | Int (Interest Payment) | UIB (Unpaid Interest Before Payment) | AO (Amount Owed) | Ad (Loan Payment) | IPmt (Interest Payment) | PPmt (Principal Payment) | UIA (Unpaid Interest After Payment) | UBA (Unpaid Balance After Payment) |
                        |------|---------------------|------------------------|---------------------------------------|------------------|-------------------|--------------------------|---------------------------|--------------------------------------|------------------------------------|
                        {table_prompt}

                        **Student Question**:
                        "{question}"

                        
                        """


        else:
            # Simple Prompt for PromptLevel = 0
            prompt = f"The student has asked the following question:\n\n{question}\nPlease provide a concise and clear response to help the student understand the concept."

        # Generate a fake Gemini response for testing purposes
        gemini_response = generate_story(prompt)

        # Append to test cases
        test_cases.append({
            "table": table,
            "story": story,
            "question": question,
            "prompt": prompt,
            "response": gemini_response,
        })

    return test_cases

def load_approved_examples(approved_examples_path):
    """
    Load the JSON file containing the approved examples/terminology.
    """
    with open(approved_examples_path, "r") as f:
        approved_examples = json.load(f)
    return approved_examples

def evaluate_responses_with_openai(approved_examples, test_cases):
    """
    Use the OpenAI API to evaluate the quality of Gemini's responses.
    :param test_cases: List of test cases with table, story, question, prompt, and response.
    :return: Evaluation results from OpenAI.
    """
    evaluations = []

    example_str = "\n".join([f"{i + 1}. {example}" for i, example in enumerate(approved_examples)])

    for idx, case in enumerate(test_cases):
        evaluation_prompt = f"""
You are an expert educator tasked with evaluating a chatbot's response to a student question in a financial engineering context. 



**Rules for Evaluation:**
- Does the response adhere to the rules provided in the chatbot's prompt?
- Does the response help the student understand the question without providing the direct answer? Be strict and harsh about this - violation of this rule should result in a score of at most 2.
- Does the response include helpful hints, formulas, or explanations without solving the blank cell?
- Is the language clear and does it match the vocabulary used in the scenario?
- The response must not include terminology or phrasing for describing financial engineering concepts outside the provided set of approved examples. Be strict and harsh about this. An example of this would be using the term 'amortization', which does not appear in the approved examples.
- The approved examples are:
 {example_str}
- Violation of this rule should result in a score of 2, at most.


Evaluate the following response on a scale of 1 to 10 in terms of quality and provide feedback.

**Scenario Context:** {case['prompt']}

**Student's Question:**
{case['question']}

**Chatbot's Response:**
{case['response']}

**Provide your Evaluation:**
- Score (1-10):
- Feedback:
"""

        try:
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=[
                    {
                        "role": "system",
                        "content": "You are a strict yet helpful grader for educational chatbots."
                    },
                    {
                        "role": "user",
                        "content": evaluation_prompt
                    }
                ],
                max_output_tokens=300,
                temperature=0.2,
            )

            evaluations.append({
                "test_case": idx + 1,
                "question": case["question"],
                "prompt": case["prompt"],
                "gemini_response": case["response"],
                "openai_evaluation": response.output_text
            })

        except Exception as e:
            evaluations.append({
                "test_case": idx + 1,
                "error": str(e)
            })

    return evaluations

approved_examples_path = "formatted_scenario_strings.json"  # Path to your JSON file with approved examples
approved_examples = load_approved_examples(approved_examples_path)

test_cases = generate_test_cases(num_cases=10, prompt_level=1, approved_examples=approved_examples)
print(test_cases)

t = True
if t:
    # Evaluate responses using OpenAI
    results = evaluate_responses_with_openai(approved_examples, test_cases)

        # Save evaluations to a file for review
    import json
    with open("gemini_evaluation_results1_5.json", "w") as f:
        json.dump(results, f, indent=4)

    print("Evaluations completed! Results saved to gemini_evaluation_results.json")