import re
from pathlib import Path

import fitz
import pytesseract
from pdf2image import convert_from_path

from config import OCR_LANG


MIN_TEXT_CHARS_PER_PAGE = 80


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def _extract_text_with_pymupdf(path: str) -> str:
    parts: list[str] = []
    with fitz.open(path) as document:
        for page in document:
            page_text = page.get_text("text")
            if page_text and len(page_text.strip()) >= MIN_TEXT_CHARS_PER_PAGE:
                parts.append(page_text)
    return _clean_text("\n\n".join(parts))


def _extract_text_with_ocr(path: str) -> str:
    images = convert_from_path(path, dpi=300)
    parts: list[str] = []
    for image in images:
        page_text = pytesseract.image_to_string(image, lang=OCR_LANG)
        if page_text.strip():
            parts.append(page_text)
    return _clean_text("\n\n".join(parts))


def extract_text_from_pdf(path: str) -> str:
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    text = _extract_text_with_pymupdf(str(pdf_path))
    if text:
        return text

    return _extract_text_with_ocr(str(pdf_path))
