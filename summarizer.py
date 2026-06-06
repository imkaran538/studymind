"""
summarizer.py
Generates structured summaries from extracted PDF text using Gemini.
"""

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

# genai is configured centrally in app.py
model = genai.GenerativeModel("gemini-1.5-flash")


def summarize(text: str, style: str = "detailed") -> str:
    """
    Summarize the provided text.
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

    # Heavy text optimization: Condense structural formatting gaps from PDFs
    clean_text = " ".join(text.split())

    prompt = f"""{instruction}

TEXT:
\"\"\"
{clean_text[:4500]}
\"\"\"

Respond only with the summary — no preamble."""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except ResourceExhausted:
        return (
            "### Quota limit exceeded\n"
            "The document provided contains too many context tokens or your Gemini free account tier has run out of points for the minute. "
            "Please try parsing a smaller snippet or wait a moment before trying again."
        )
    except Exception as e:
        return f"An error occurred while building your summary: {str(e)}"
