import json

from google import genai

PROMPT = """
  Based on the following transcript, generate a quiz in valid JSON format.

  The quiz must follow this exact structure:

  {
    "title": "Create a concise quiz title based on the topic of the transcript.",
    "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",
    "questions": [
      {
        "question_title": "The question goes here.",
        "question_options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": "The correct answer from the above options"
      },
      ...
      (exactly 10 questions)
    ]
  }

  Requirements:
  - Each question must have exactly 4 distinct answer options.
  - Only one correct answer is allowed per question, and it must be present in 'question_options'.
  - The output must be valid JSON and parsable as-is (e.g., using Python's json.loads).
  - Do not include explanations, comments, or any text outside the JSON.

  Transcript:
"""


def generate_quiz(transcript: str) -> dict:
    client = genai.Client()

    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=PROMPT + transcript,
    )

    text = interaction.output_text.strip()

    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()

    return json.loads(text)
