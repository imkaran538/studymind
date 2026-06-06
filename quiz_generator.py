"""
quiz_generator.py
Generates MCQ and short-answer quizzes from study material using Gemini.
"""

import json
import re
import google.generativeai as genai

# genai is configured centrally in app.py
model = genai.GenerativeModel("gemini-2.0-flash")


def generate_mcq(text: str, num_questions: int = 5) -> list[dict]:
    """
    Generate multiple-choice questions.

    Returns a list of dicts:
        {
          "question": str,
          "options": {"A": str, "B": str, "C": str, "D": str},
          "answer": "A" | "B" | "C" | "D",
          "explanation": str
        }
    """
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
{text[:5000]}
\"\"\"
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return [{"question": "Could not parse quiz. Please try again.", "options": {}, "answer": "", "explanation": ""}]


def generate_short_answer(text: str, num_questions: int = 5) -> list[dict]:
    """
    Generate short-answer questions.

    Returns a list of dicts:
        {
          "question": str,
          "sample_answer": str
        }
    """
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
{text[:5000]}
\"\"\"
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return [{"question": "Could not parse quiz. Please try again.", "sample_answer": ""}]


def evaluate_answer(question: str, user_answer: str, sample_answer: str) -> dict:
    """
    Use Gemini to evaluate a user's short answer against the sample answer.
    Returns {"score": int (0-10), "feedback": str}
    """
    prompt = f"""Evaluate this student's answer.

Question: {question}
Sample Answer: {sample_answer}
Student Answer: {user_answer}

Score the student's answer from 0 to 10 based on accuracy and completeness.
Return ONLY a JSON object: {{"score": <int>, "feedback": "<one sentence feedback>"}}
No markdown, no extra text."""

    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"score": 0, "feedback": "Could not evaluate answer."}
