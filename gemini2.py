from google import genai
from google.genai import types
import os
import time
from pathlib import Path

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

# -------------------------
# 1) Create a File Search store (persistent index container)
# -------------------------
file_search_store = client.file_search_stores.create(
    config={"display_name": "ie201-lecture-materials"}
)
print("Created store:", file_search_store.name)

# -------------------------
# 2) Upload lecture materials into the store (indexing happens here)
#    Put your PDFs/txts in a folder like ./ie201_materials/
# -------------------------
materials_dir = Path("ie201_materials")
files_to_upload = [
    p for p in materials_dir.glob("*")
    if p.suffix.lower() in {".pdf", ".txt", ".md"}
]

if not files_to_upload:
    raise RuntimeError(
        f"No files found in {materials_dir.resolve()}. "
        "Add PDFs/TXTs/MDs and rerun."
    )

for path in files_to_upload:
    print("Uploading:", path.name)

    operation = client.file_search_stores.upload_to_file_search_store(
        file=str(path),
        file_search_store_name=file_search_store.name,
        config={
            # This name shows up in citations
            "display_name": path.name,

            # Optional: tune chunking (uncomment if you want smaller chunks)
            # "chunking_config": {
            #     "white_space_config": {
            #         "max_tokens_per_chunk": 300,
            #         "max_overlap_tokens": 40
            #     }
            # },
        },
    )

    # Wait for indexing to finish
    while not operation.done:
        time.sleep(5)
        operation = client.operations.get(operation)

print("All files indexed into:", file_search_store.name)

# -------------------------
# 3) Ask questions with File Search enabled
# -------------------------
system_style = """
You are an IE201 (Engineering Economics) tutor.
Use File Search to ground your answers in the indexed lecture materials.
If the materials don't contain the needed info, say so and then answer generally.
When possible, show steps and clearly state assumptions (timing, sign convention, i, n).
"""

question = "What are the ten principles of engineering economy."

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=f"{system_style}\n\nStudent question: {question}",
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(
                file_search=types.FileSearch(
                    file_search_store_names=[file_search_store.name]
                )
            )
        ]
    ),
)

print(response.text)
