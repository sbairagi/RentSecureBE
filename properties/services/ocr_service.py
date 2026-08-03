"""PDF OCR and text extraction utilities for Form 16 and rent receipts."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Try to use pdfplumber for text extraction; fall back gracefully if unavailable.
try:
    import pdfplumber  # type: ignore[import-untyped]

    HAS_PDFPLUMBER = True
except Exception:  # pragma: no cover - optional dependency
    pdfplumber = None  # type: ignore[assignment]
    HAS_PDFPLUMBER = False


def extract_pdf_text(file: Any) -> str:
    """Extract text from a PDF file using pdfplumber.

    Args:
        file: Uploaded file object or file-like object.

    Returns:
        Extracted text as a single string.
    """
    if not HAS_PDFPLUMBER:
        raise RuntimeError(
            "pdfplumber is not installed. Install it with: pip install pdfplumber"
        )

    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        logger.exception("Failed to extract text from PDF.")
        raise
    return text


def extract_pan(text: str) -> str:
    """Extract PAN number from text using regex."""
    match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]", text)
    return match.group(0) if match else ""


def extract_salary(text: str) -> float:
    """Extract gross/total salary from Form 16 text."""
    patterns = [
        r"Gross Salary[^\d]*(\d[\d,]+)",
        r"Total Earnings[^\d]*(\d[\d,]+)",
        r"Basic Salary[^\d]*(\d[\d,]+)",
        r"Gross Amount[^\d]*(\d[\d,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))
    return 0.0


def extract_hra(text: str) -> float:
    """Extract HRA received from Form 16 text."""
    patterns = [
        r"HRA[^\d]*(\d[\d,]+)",
        r"House Rent Allowance[^\d]*(\d[\d,]+)",
        r"Allowance[^\d]*HRA[^\d]*(\d[\d,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))
    return 0.0


def extract_rent_paid(text: str) -> float:
    """Extract rent paid from rent receipt or Form 16 text."""
    patterns = [
        r"Rent Paid[^\d]*(\d[\d,]+)",
        r"Total Rent[^\d]*(\d[\d,]+)",
        r"Rent[^\d]*(\d[\d,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))
    return 0.0


def extract_form16_data(file: Any) -> dict[str, Any]:
    """Extract key ITR data from an uploaded Form 16 / rent receipt PDF.

    Args:
        file: Uploaded PDF file object.

    Returns:
        dict with keys: pan, salary, hra_received, rent_paid, raw_text
    """
    text = ""
    try:
        text = extract_pdf_text(file)
    except Exception as exc:
        logger.exception("PDF text extraction failed: %s", exc)
        return {
            "pan": "",
            "salary": 0.0,
            "hra_received": 0.0,
            "rent_paid": 0.0,
            "raw_text": "",
            "error": f"PDF text extraction failed: {exc}",
        }

    pan = extract_pan(text)
    salary = extract_salary(text)
    hra = extract_hra(text)
    rent_paid = extract_rent_paid(text)

    return {
        "pan": pan,
        "salary": salary,
        "hra_received": hra,
        "rent_paid": rent_paid,
        "raw_text": text,
        "error": None,
    }
