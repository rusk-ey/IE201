import json
from genai_story_generator import generate_story

# Define the shared prompt to generate stories
STORY_PROMPT = (
    "Write a short word problem about a business or person who borrows ${initial_balance} at an annual interest "
    "rate of {interest_rate}%. Payments are deferred for {deferment_years} years before entering repayment. "
    "The repayment plan involves annual payments of ${loan_payment} over {repayment_years} years. "
    "Describe the loan, deferral period, deferment years, and repayment terms without including explanations or solutions."
)

# Output file for generated strings
OUTPUT_FILE = "formatted_scenario_strings.json"

def generate_and_store_scenarios():
    """
    Generate and append additional formatted scenarios to a JSON file.
    """
    # Placeholder for new scenarios
    new_generated_scenarios = []

    # Generate the scenarios
    for i in range(5):  # Change the range to generate as many stories as you'd like
        print(f"Generating scenario {i + 1}...")
        try:
            # Submit the STORY_PROMPT to Gemini
            scenario = generate_story(STORY_PROMPT)
            print(f"Generated Scenario {i + 1}: {scenario.strip()}")  # Debugging: Print each output
            new_generated_scenarios.append(scenario.strip())
        except Exception as e:
            print(f"Error generating scenario {i + 1}: {e}")
            new_generated_scenarios.append("An error occurred while generating this scenario.")

    # Load existing data from the file if it exists
    try:
        with open(OUTPUT_FILE, "r") as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        print(f"No existing file found. Creating a new one: {OUTPUT_FILE}")
        existing_data = []

    # Append the new scenarios to the existing data
    all_scenarios = existing_data + new_generated_scenarios

    # Save updated data back to the file
    try:
        with open(OUTPUT_FILE, "w") as f:
            json.dump(all_scenarios, f, indent=4)
        print(f"\nSuccess! Total of {len(all_scenarios)} scenarios have been saved to '{OUTPUT_FILE}'.")
    except Exception as e:
        print(f"Error saving stories to file: {e}")


if __name__ == "__main__":
    generate_and_store_scenarios()