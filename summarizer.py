"""
summarizer.py
Generates structured summaries from extracted PDF text using Gemini.
"""

import google.generativeai as genai

# genai is configured centrally in app.py
model = genai.GenerativeModel("gemini-1.5-flash")


def summarize(text: str, style: str = "detailed") -> str:
    """
    Summarize the provided text.

    style options:
        "brief"    – 3-5 sentence TL;DR
        "detailed" – section-by-section breakdown with key points
        "bullets"  – bullet-point highlights
    """
    style_instructions = {
        "brief": (
            "Write a concise 3-5 sentence summary that captures the most "
            "important idea of the text."
        ),
        "detailed": (
            "Write a detailed summary organized by topic. Use clear headings "
            "for each major section and list the key points under each heading."
        ),
        "bullets": (
            "List the 10 most important facts or concepts from the text as "
            "clear, numbered bullet points. Each point should be self-contained."
        ),
    }

    instruction = style_instructions.get(style, style_instructions["detailed"])

    prompt = f"""{instruction}

TEXT:
\"\"\"
{text[:6000]}
\"\"\"

Respond only with the summary — no preamble."""

    response = model.generate_content(prompt)
    return response.text.strip()
