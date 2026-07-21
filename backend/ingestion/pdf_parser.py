import fitz  # PyMuPDF
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import CHUNK_SIZE, CHUNK_OVERLAP


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a PDF file.
    Uses PyMuPDF (fitz) to read each page.
    """
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            full_text += f"\n--- Page {page_num + 1} ---\n{text}"
        
        doc.close()
        return full_text.strip()
    
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, 
               overlap: int = CHUNK_OVERLAP) -> list:
    """
    Break large text into smaller overlapping chunks.
    
    Why overlap? If a sentence is split across two chunks,
    overlap ensures the meaning is preserved in both.
    """
    words = text.split()
    chunks = []
    
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap  # overlap with previous chunk
    
    return chunks


def get_document_metadata(filename: str) -> dict:
    """
    Determine metadata for a document based on its filename.
    This tells us which regulatory body the document belongs to.
    """
    filename_lower = filename.lower()
    
    if "oisd" in filename_lower:
        regulatory_body = "OISD"
        doc_type = "regulatory"
        
        if "105" in filename_lower:
            topic = "work_permit_system"
            description = "OISD Standard 105 - Work Permit System"
        elif "106" in filename_lower:
            topic = "pressure_relief"
            description = "OISD Standard 106 - Pressure Relief Devices"
        elif "116" in filename_lower:
            topic = "fire_protection"
            description = "OISD Standard 116 - Fire Protection"
        elif "137" in filename_lower:
            topic = "electrical_inspection"
            description = "OISD Standard 137 - Electrical Equipment Inspection"
        else:
            topic = "general_safety"
            description = f"OISD Standard - {filename}"
            
    elif "factories" in filename_lower:
        regulatory_body = "Ministry of Labour"
        doc_type = "regulatory"
        topic = "factory_safety_law"
        description = "Factories Act 1948 - Primary industrial safety legislation"
        
    elif "dgms" in filename_lower:
        regulatory_body = "DGMS"
        doc_type = "regulatory"
        topic = "mines_safety"
        description = "DGMS Safety Guidelines"
        
    elif "peso" in filename_lower:
        regulatory_body = "PESO"
        doc_type = "regulatory"
        topic = "explosives_safety"
        description = "PESO Guidelines"
        
    else:
        regulatory_body = "Unknown"
        doc_type = "operational"
        topic = "general"
        description = filename
    
    return {
        "source": filename,
        "regulatory_body": regulatory_body,
        "doc_type": doc_type,
        "topic": topic,
        "description": description
    }


def process_pdf(pdf_path: str) -> list:
    """
    Complete pipeline for one PDF:
    1. Extract text
    2. Chunk it
    3. Attach metadata to each chunk
    
    Returns list of dicts ready for ChromaDB storage.
    """
    filename = os.path.basename(pdf_path)
    print(f"Processing: {filename}")
    
    # Step 1 - Extract text
    from ingestion.ocr_parser import extract_text_smart
    text = extract_text_smart(pdf_path)
    
    if not text:
        print(f"Warning: No text extracted from {filename}")
        return []
    
    print(f"Extracted {len(text.split())} words from {filename}")
    
    # Step 2 - Chunk text
    chunks = chunk_text(text)
    print(f"Created {len(chunks)} chunks from {filename}")
    
    # Step 3 - Attach metadata
    metadata = get_document_metadata(filename)
    
    processed_chunks = []
    for i, chunk in enumerate(chunks):
        processed_chunks.append({
            "text": chunk,
            "metadata": {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_id": f"{filename}_chunk_{i}"
            }
        })
    
    return processed_chunks


if __name__ == "__main__":
    # Test with one PDF
    import sys
    sys.path.append("..")
    from core.config import REGULATORY_DIR
    
    test_pdf = os.path.join(REGULATORY_DIR, "factories_act_1948.pdf")
    
    if os.path.exists(test_pdf):
        chunks = process_pdf(test_pdf)
        print(f"\nTotal chunks: {len(chunks)}")
        print(f"\nFirst chunk preview:")
        print(chunks[0]['text'][:300])
        print(f"\nMetadata: {chunks[0]['metadata']}")
    else:
        print(f"File not found: {test_pdf}")
        