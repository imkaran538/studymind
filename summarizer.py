"""
summarizer.py
Generates structured summaries from extracted PDF text using Gemini.
"""

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

# Updated to use a current active stable model
model = genai.GenerativeModel("gemini-3.1-flash-lite")


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
            "Provide a comprehensive, highly accurate summary of this entire document. "
            "Organize your summary sequentially by its major topics/chapters. Use bold Markdown "
            "headings for each major section, and list detailed key points, data points, or "
            "conclusions reached within that section. Maintain strict factual alignment with the source."
        ),
        "bullets": (
            "List the 10 most important facts or concepts from the text as "
            "clear, numbered bullet points. Each point should be self-contained."
        ),
    }

    instruction = style_instructions.get(style, style_instructions["detailed"])

    # Compress structural gaps from parsed PDFs
    clean_text = " ".join(text.split())

    prompt = f"""{instruction}

TEXT:
\"\"\"
{clean_text[:10000]}
\"\"\"
Respond only with the summary — no preamble."""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except ResourceExhausted:
        return (
            "### Quota limit exceeded\n"
            "The document provided contains too many context tokens or your Gemini account tier has run out of units. "
            "Please try parsing a smaller snippet or wait a moment before trying again."
        )
    except Exception as e:
        return f"An error occurred while building your summary: {str(e)}"
