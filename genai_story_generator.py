from google import genai
import os

# Initialize the GenAI client
client = genai.Client(
    api_key=os.environ["GOOGLE_API_KEY"]  # Ensure your API key is set as an environment variable
)

def generate_story(prompt):
    """Generate a story using the Gemini API with fallback for overload errors."""
    try:
        print(f"Sending Prompt to Gemini: {prompt}")  # Debugging: Confirm the prompt being sent
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
        )
        print(f"Gemini response received: {response.text}")  # Debugging: Print API response
        return response.text.strip()  # Return story content, trim whitespaces
    except Exception as e:
        # Handle specific API errors and exceptions
        if isinstance(e, genai.errors.APIError) and e.code == 503:
            print("Gemini API is currently overloaded. Falling back.")
            return (
                "The story generation system is currently overloaded and experiencing high traffic. "
                "Please try again later."
            )
        else:
            print(f"An unexpected error occurred while generating the story: {e}")
            return "An error occurred while generating the story. Please contact support."