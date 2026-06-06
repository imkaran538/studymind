"""
planner.py
Generates a day-by-day study plan from topics + deadline using Gemini.
"""

import google.generativeai as genai

# genai is configured centrally in app.py
model = genai.GenerativeModel("gemini-1.5-flash")


def generate_plan(topics: list[str], days_available: int, hours_per_day: float, exam_name: str = "Exam") -> str:
    """
    Generate a structured study plan.

    Args:
        topics: list of topic strings to cover
        days_available: number of days until exam
        hours_per_day: hours the student can study each day
        exam_name: name of the exam or subject

    Returns:
        Markdown-formatted study plan as a string.
    """
    topics_str = "\n".join(f"- {t}" for t in topics)
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

    response = model.generate_content(prompt)
    return response.text.strip()


def ask_doubt(context: str, question: str) -> str:
    """
    Answer a student's doubt based on the study material context.
    """
    prompt = f"""You are a helpful tutor. Answer the student's question based on the provided study material.
Be clear, concise, and encouraging. If the answer isn't in the material, say so and give a general answer.

STUDY MATERIAL (excerpt):
\"\"\"
{context[:4000]}
\"\"\"

STUDENT QUESTION: {question}

Answer:"""

    response = model.generate_content(prompt)
    return response.text.strip()
