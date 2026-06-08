import re
from functools import lru_cache
from pathlib import Path

import fitz
import numpy as np
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError

from app.config import OCR_LANG


MIN_TEXT_CHARS_PER_PAGE = 80

EASYOCR_LANGUAGE_MAP = {
    "fra": "fr",
    "fre": "fr",
    "eng": "en",
}


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
    try:
        images = convert_from_path(path, dpi=300)
    except PDFInfoNotInstalledError as exc:
        raise RuntimeError(
            "OCR PDF indisponible: installez poppler-utils pour fournir `pdfinfo`."
        ) from exc

    reader = _get_easyocr_reader()
    parts: list[str] = []
    for image in images:
        image_array = np.array(image)
        page_text = "\n".join(reader.readtext(image_array, detail=0, paragraph=True))
        if page_text.strip():
            parts.append(page_text)
    return _clean_text("\n\n".join(parts))


@lru_cache(maxsize=1)
def _get_easyocr_reader():
    try:
        import easyocr
    except ImportError as exc:
        raise RuntimeError(
            "OCR PDF indisponible: installez la dependance Python `easyocr`."
        ) from exc

    language = EASYOCR_LANGUAGE_MAP.get(OCR_LANG.lower(), OCR_LANG.lower())
    try:
        return easyocr.Reader([language], gpu=False)
    except ValueError as exc:
        raise RuntimeError(
            f"Langue OCR non prise en charge par EasyOCR: `{OCR_LANG}`."
        ) from exc


def extract_text_from_pdf(path: str) -> str:
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    text = _extract_text_with_pymupdf(str(pdf_path))
    if text:
        return text

    return _extract_text_with_ocr(str(pdf_path))
