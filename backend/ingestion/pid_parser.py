import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re


def extract_labels_from_svg(svg_path: str) -> list:
    """
    Extract text labels (equipment tags, instrument tags, process data)
    from a vector-based P&ID/engineering drawing in SVG format.
    Works when the drawing was created in a vector tool (Inkscape, AutoCAD export, etc.)
    where labels remain as real text elements, not rasterized images.
    """
    with open(svg_path, 'r', encoding='utf-8') as f:
        content = f.read()

    raw_labels = re.findall(r'<text[^>]*>(.*?)</text>', content, re.DOTALL)
    labels = []
    for label in raw_labels:
        clean = re.sub(r'<[^>]+>', '', label).strip()
        if clean:
            labels.append(clean)

    return labels


def extract_labels_from_drawing(file_path: str) -> list:
    """
    Smart wrapper: extracts text labels from an engineering drawing,
    regardless of whether it's a vector SVG or a scanned/rasterized image.
    """
    if file_path.endswith('.svg'):
        return extract_labels_from_svg(file_path)

    elif file_path.endswith('.pdf'):
        from ingestion.ocr_parser import extract_text_smart
        text = extract_text_smart(file_path)
        # Split OCR output into individual lines/labels for consistency
        return [line.strip() for line in text.split('\n') if line.strip()]

    else:
        print(f"Unsupported drawing format: {file_path}")
        return []


def drawing_labels_to_chunk(file_path: str) -> dict:
    """
    Convert extracted drawing labels into a chunk format
    compatible with the rest of the ingestion pipeline.
    """
    filename = os.path.basename(file_path)
    labels = extract_labels_from_drawing(file_path)

    if not labels:
        return None

    text = f"Engineering Drawing: {filename}\nExtracted Labels:\n" + "\n".join(labels)

    return {
        "text": text,
        "metadata": {
            "source": filename,
            "chunk_id": f"drawing_{os.path.splitext(filename)[0]}",
            "doc_type": "engineering_drawing","symbol_detection_done": False
        }
    }
