"""
quiz_generator.py
Generates MCQ and short-answer quizzes from study material using Gemini.
"""

import json
import re
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

# genai is configured centrally in app.py
model = genai.GenerativeModel("gemini-1.5-flash")

def clean_input_text(text: str) -> str:
    """Helper to remove duplicate lines/spaces from PDF parsing."""
    return " ".join(text.split())

def generate_mcq(text: str, num_questions: int = 5) -> list[dict]:
    """
    Generate multiple-choice questions.
    """
    clean_text = clean_input_text(text)
    prompt = f"""You are a quiz maker. Based on the text below, create exactly {num_questions} multiple-choice questions.

Rules:
- Each question must have 4 options labelled A, B, C, D.
- Only one option is correct.
- Include a one-sentence explanation for the correct answer.
- Return ONLY a valid JSON array — no markdown fences, no extra text.

JSON format:
[
  {{
    "question": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "answer": "A",
    "explanation": "..."
  }}
]

TEXT:
\"\"\"
{clean_text[:4000]}
\"\"\"
"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        return json.loads(raw)
    except ResourceExhausted:
        return [{"question": "The quiz generator is out of temporary free tokens. Please wait 30-60 seconds and hit submit again.", "options": {}, "answer": "", "explanation": ""}]
    except (json.JSONDecodeError, Exception):
        return [{"question": "Could not parse quiz. Please try again with a different portion of text.", "options": {}, "answer": "", "explanation": ""}]


def generate_short_answer(text: str, num_questions: int = 5) -> list[dict]:
    """
    Generate short-answer questions.
    """
    clean_text = clean_input_text(text)
    prompt = f"""You are a quiz maker. Based on the text below, create exactly {num_questions} short-answer questions.

Rules:
- Questions should require a 1-3 sentence answer.
- Include a model sample answer.
- Return ONLY a valid JSON array — no markdown fences, no extra text.

JSON format:
[
  {{
    "question": "...",
    "sample_answer": "..."
  }}
]

TEXT:
\"\"\"
{clean_text[:4000]}
\"\"\"
"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        return json.loads(raw)
    except ResourceExhausted:
        return [{"question": "The quiz generator is out of temporary free tokens. Please try again shortly.", "sample_answer": ""}]
    except (json.JSONDecodeError, Exception):
        return [{"question": "Could not parse short answer quiz. Please try again.", "sample_answer": ""}]


def evaluate_answer(question: str, user_answer: str, sample_answer: str) -> dict:
    """
    Use Gemini to evaluate a user's short answer against the sample answer.
    """
    prompt = f"""Evaluate this student's answer.

Question: {question}
Sample Answer: {sample_answer}
Student Answer: {user_answer}

Score the student's answer from 0 to 10 based on accuracy and completeness.
Return ONLY a JSON object: {{"score": <int>, "feedback": "<one sentence feedback>"}}
No markdown, no extra text."""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        return json.loads(raw)
    except ResourceExhausted:
        return {"score": 0, "feedback": "Evaluation system busy due to quota constraints. Try resubmitting."}
    except (json.JSONDecodeError, Exception):
        return {"score": 0, "feedback": "Could not evaluate answer framework structural error."}
