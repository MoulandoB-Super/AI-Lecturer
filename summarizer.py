"""
summarizer.py — Generate structured lecture notes using Claude (Anthropic)
"""

import anthropic

client = anthropic.Anthropic()

# Max characters to send to Claude (~100k tokens safety margin)
MAX_TEXT_LENGTH = 80_000


def generate_notes(text: str) -> str:
    """
    Convert raw lecture text (from PDF or YouTube transcript)
    into clean, structured markdown notes using Claude.

    Args:
        text: Raw lecture/transcript text.

    Returns:
        Formatted markdown notes as a string.

    Raises:
        ValueError: If text is empty.
        RuntimeError: If the API call fails.
    """
    if not text or not text.strip():
        raise ValueError("Cannot generate notes from empty text.")

    # Truncate if too long, keeping the beginning and end
    if len(text) > MAX_TEXT_LENGTH:
        half = MAX_TEXT_LENGTH // 2
        text = (
            text[:half]
            + "\n\n...[content trimmed for length]...\n\n"
            + text[-half:]
        )

    prompt = f"""You are an expert academic note-taker. Below is raw text from a lecture or educational video.

Transform it into clean, well-structured lecture notes in Markdown format.

Your notes MUST include these sections:

## 📋 Summary
A clear 3-5 sentence overview of what the lecture covers.

## 🔑 Key Points
The most important ideas, each explained in 1-2 sentences.

## 💡 Important Concepts
Core terms, definitions, frameworks, or theories introduced. Bold each term.

## 🔗 How It All Connects
A short paragraph explaining how the key ideas relate to each other.

## ❓ Practice Questions
Exactly 5 questions a student could use to test their understanding. Number them.

---

Rules:
- Use clear, concise language — avoid repeating the source text verbatim
- Use bullet points and bold text to make notes scannable
- If the text is unclear or incomplete, note that briefly
- Write for a student who missed the lecture

Lecture text:
\"\"\"
{text}
\"\"\"

Lecture Notes:"""

    try:
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    except anthropic.AuthenticationError:
        raise RuntimeError(
            "Invalid Anthropic API key. Set the ANTHROPIC_API_KEY environment variable."
        )
    except anthropic.RateLimitError:
        raise RuntimeError(
            "Rate limit reached. Please wait a moment and try again."
        )
    except anthropic.APIStatusError as e:
        raise RuntimeError(f"Anthropic API error ({e.status_code}): {e.message}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error generating notes: {str(e)}")
