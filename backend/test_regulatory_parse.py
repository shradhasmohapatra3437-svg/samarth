import sys, os
sys.path.insert(0, '.')
from ingestion.pdf_parser import process_pdf

files = [
    '../data/regulatory/oisd_std_137.pdf',
    '../data/regulatory/oisd_std_105.pdf',
    '../data/regulatory/oisd_std_116.pdf',
    '../data/regulatory/oisd_std_106.pdf',
    '../data/regulatory/factories_act_1948.pdf',
    '../data/regulatory/peso_rules.pdf',
    '../data/regulatory/cpcb_environmental_norms.pdf',
    '../data/regulatory/dgms_safety_guidelines.pdf',
]

total_chunks = 0
for f in files:
    name = os.path.basename(f)
    chunks = process_pdf(f)
    total_chunks += len(chunks)
    char_count = sum(len(c['text']) for c in chunks)
    print(f"{name} -> {len(chunks)} chunks, ~{char_count} characters")

print(f"\nTOTAL: {total_chunks} regulatory document chunks parsed successfully.")
