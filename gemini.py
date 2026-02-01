from google import genai
import os

client = genai.Client(
    api_key=os.environ["GOOGLE_API_KEY"]
)

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="What are the ten principles of engineering economy",
)

print(response.text)