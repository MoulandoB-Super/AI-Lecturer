"""
pdf_reader.py — Extract clean text from PDF files using pypdf
"""

import re
from pypdf import PdfReader


# Max pages to process (safety limit for huge PDFs)
MAX_PAGES = 200


def extract_text(file) -> str:
    """
    Extract and clean all text from a PDF file.

    Args:
        file: A file-like object (e.g. from FastAPI's UploadFile or io.BytesIO).

    Returns:
        Cleaned text as a single string.

    Raises:
        ValueError: If the PDF is empty, encrypted, or has no extractable text.
        RuntimeError: If the PDF cannot be read.
    """
    try:
        reader = PdfReader(file)
    except Exception as e:
        raise RuntimeError(f"Could not open PDF file: {str(e)}")

    # Handle password-protected PDFs
    if reader.is_encrypted:
        raise ValueError(
            "This PDF is password-protected. Please provide an unlocked PDF."
        )

    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("The PDF has no pages.")

    # Warn if truncating
    pages_to_read = min(total_pages, MAX_PAGES)

    extracted_pages = []

    for i in range(pages_to_read):
        try:
            page_text = reader.pages[i].extract_text() or ""
            page_text = _clean_text(page_text)
            if page_text:
                extracted_pages.append(f"[Page {i + 1}]\n{page_text}")
        except Exception:
            # Skip unreadable pages silently, don't crash
            continue

    if not extracted_pages:
        raise ValueError(
            "No text could be extracted from this PDF. "
            "It may be a scanned image-only PDF without OCR."
        )

    full_text = "\n\n".join(extracted_pages)

    # Append truncation notice if needed
    if total_pages > MAX_PAGES:
        full_text += (
            f"\n\n[Note: Only the first {MAX_PAGES} of {total_pages} pages were processed.]"
        )

    return full_text


def _clean_text(text: str) -> str:
    """
    Clean extracted page text:
    - Normalize whitespace and line breaks
    - Remove null bytes and control characters
    - Collapse excessive blank lines
    """
    if not text:
        return ""

    # Remove null bytes and non-printable control characters (keep newlines/tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Normalize unicode spaces
    text = text.replace("\xa0", " ").replace("\u200b", "")

    # Collapse 3+ blank lines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove lines that are just whitespace
    lines = [line if line.strip() else "" for line in text.splitlines()]
    text = "\n".join(lines)

    # Collapse multiple spaces into one (but preserve indentation loosely)
    text = re.sub(r"[ \t]{3,}", "  ", text)

    return text.strip()


def get_page_count(file) -> int:
    """Return the number of pages in a PDF without extracting text."""
    try:
        reader = PdfReader(file)
        return len(reader.pages)
    except Exception as e:
        raise RuntimeError(f"Could not read PDF: {str(e)}")
