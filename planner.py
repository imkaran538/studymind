"""
planner.py
Generates a day-by-day study plan from topics + deadline using Gemini.
"""

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

# Updated to use a current active stable model
model = genai.GenerativeModel("gemini-2.5-flash")


def generate_plan(topics: list[str], days_available: int, hours_per_day: float, exam_name: str = "Exam") -> str:
    """
    Generate a structured study plan.
    """
    topics_str = "\n".join(f"- {t.strip()}" for t in topics if t.strip())
    total_hours = days_available * hours_per_day

    prompt = f"""You are an expert academic coach. Create a practical, day-by-day study plan for a student.

Exam / Subject: {exam_name}
Days until exam: {days_available}
Hours per day: {hours_per_day:.1f}
Total study hours: {total_hours:.1f}

Topics to cover:
{topics_str}

Guidelines:
1. Distribute topics logically — related concepts together.
2. Schedule revision days before the exam.
3. Include short breaks/self-care reminders.
4. Format the plan as a clean day-by-day schedule using Markdown.
5. Each day entry should include: Day number, Date label (Day 1, Day 2...), Topics, Goal for the day, and a tip.
6. End with a motivational message.

Return only the study plan — no preamble."""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except ResourceExhausted:
        return (
            "## Quota Limit Reached\n"
            "The study planner is currently experiencing high demand or free-tier quota limits. "
            "Please wait a minute or two and try generating your study plan again."
        )
    except Exception as e:
        return f"An error occurred while generating your plan: {str(e)}"


def ask_doubt(context: str, question: str) -> str:
    """
    Answer a student's doubt based on the study material context.
    """
    clean_context = " ".join(context.split())

    prompt = f"""You are a helpful tutor. Answer the student's question based on the provided study material.
Be clear, concise, and encouraging. If the answer isn't in the material, say so and give a general answer.

STUDY MATERIAL (excerpt):
\"\"\"
{clean_context[:3000]}
\"\"\"

STUDENT QUESTION: {question}

Answer:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except ResourceExhausted:
        return "I am temporarily unable to answer doubts due to API rate limits. Please try your question again in a moment!"
    except Exception as e:
        return f"Could not fetch an answer due to an unexpected error: {str(e)}"
