"""
app.py — FastAPI backend for AI Lecture Notes Generator
Run: uvicorn app:app --reload
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from pdf_reader import extract_text
from summarizer import generate_notes
from youtube_transcript import get_transcript

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Lecture Notes Generator",
    description="Generate smart notes from PDFs and YouTube lectures.",
    version="1.0.0",
)

# ── CORS (allows the HTML frontend to call this API) ────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restrict to your domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global error handler ────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected server error occurred. Please try again."},
    )

# ── Health check ────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Quick check that the server is up."""
    return {"status": "ok"}

# ── PDF endpoint ─────────────────────────────────────────────────────────────
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Accept a PDF file and return AI-generated lecture notes.
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Validate file size (max 20 MB)
    MAX_SIZE = 20 * 1024 * 1024
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 20 MB.")

    logger.info(f"Processing PDF: {file.filename} ({len(contents):,} bytes)")

    try:
        import io
        text = extract_text(io.BytesIO(contents))
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {str(e)}")

    if not text or not text.strip():
        raise HTTPException(
            status_code=422,
            detail="The PDF appears to be empty or image-only (no extractable text).",
        )

    try:
        notes = generate_notes(text)
    except Exception as e:
        logger.error(f"Note generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate notes: {str(e)}")

    logger.info(f"Notes generated for: {file.filename}")
    return {"notes": notes, "filename": file.filename}


# ── YouTube endpoint ──────────────────────────────────────────────────────────
@app.get("/youtube-notes")
async def youtube_notes(url: str):
    """
    Accept a YouTube URL and return AI-generated lecture notes.
    """
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="Please provide a YouTube URL.")

    if "youtube.com" not in url and "youtu.be" not in url:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL.")

    logger.info(f"Processing YouTube URL: {url}")

    try:
        transcript = get_transcript(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Transcript fetch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch transcript: {str(e)}")

    if not transcript or not transcript.strip():
        raise HTTPException(
            status_code=422,
            detail="Transcript is empty. The video may not have captions.",
        )

    try:
        notes = generate_notes(transcript)
    except Exception as e:
        logger.error(f"Note generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate notes: {str(e)}")

    logger.info(f"Notes generated for: {url}")
    return {"notes": notes, "url": url}
