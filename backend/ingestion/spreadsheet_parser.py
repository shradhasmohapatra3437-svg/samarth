import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from core.config import CHUNK_SIZE, CHUNK_OVERLAP


def extract_rows_from_spreadsheet(file_path: str) -> list:
    """
    Read an Excel (.xlsx) or CSV file and convert each row into
    a structured text chunk, similar to how JSON records are processed.
    """
    filename = os.path.basename(file_path)

    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error reading spreadsheet {filename}: {e}")
        return []

    chunks = []
    for idx, row in df.iterrows():
        row_text = "\n".join([f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])])
        chunk_id = f"{os.path.splitext(filename)[0]}_row{idx}"

        chunks.append({
            "text": row_text,
            "metadata": {
                "source": filename,
                "chunk_id": chunk_id,
                "row_number": idx
            }
        })

    print(f"Extracted {len(chunks)} rows from {filename}")
    return chunks
