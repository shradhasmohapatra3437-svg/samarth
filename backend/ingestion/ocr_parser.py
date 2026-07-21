import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytesseract
from pdf2image import convert_from_path
from core.config import CHUNK_SIZE, CHUNK_OVERLAP

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler\poppler-26.02.0\Library\bin"


def is_scanned_pdf(pdf_path: str, min_chars_threshold: int = 50) -> bool:
    import fitz
    doc = fitz.open(pdf_path)
    first_page_text = doc[0].get_text() if doc.page_count > 0 else ""
    doc.close()
    return len(first_page_text.strip()) < min_chars_threshold


def extract_text_via_ocr(pdf_path: str) -> str:
    try:
        pages = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
        full_text = ""

        for page_num, page_image in enumerate(pages):
            text = pytesseract.image_to_string(page_image)
            full_text += f"\n--- Page {page_num + 1} (OCR) ---\n{text}"

        return full_text.strip()

    except Exception as e:
        print(f"Error during OCR extraction for {pdf_path}: {e}")
        return ""


def extract_text_smart(pdf_path: str) -> str:
    from ingestion.pdf_parser import extract_text_from_pdf

    if is_scanned_pdf(pdf_path):
        print(f"'{os.path.basename(pdf_path)}' appears scanned — using OCR...")
        return extract_text_via_ocr(pdf_path)
    else:
        return extract_text_from_pdf(pdf_path)
    