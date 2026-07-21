import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_json_file(filepath: str) -> list:
    """Load a JSON file and return its contents."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} records from {os.path.basename(filepath)}")
        return data
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return []


def process_work_orders(data: list) -> list:
    """
    Convert work order records into text chunks for ChromaDB.
    Each work order becomes one chunk with its metadata.
    """
    chunks = []
    
    for record in data:
        # Convert record to readable text
        text = f"""
Work Order: {record.get('work_order_id', '')}
Equipment: {record.get('equipment_tag', '')}
Date: {record.get('date', '')}
Failure: {record.get('failure_description', '')}
Technician: {record.get('technician_assigned', '')}
Resolution: {record.get('resolution_notes', '')}
OISD Reference: {record.get('oisd_reference', '')}
Downtime: {record.get('downtime_hours', '')} hours
Status: {record.get('status', '')}
        """.strip()
        
        chunks.append({
            "text": text,
            "metadata": {
                "source": "work_orders.json",
                "doc_type": "operational",
                "record_type": "work_order",
                "equipment_tag": record.get('equipment_tag', ''),
                "date": record.get('date', ''),
                "technician": record.get('technician_assigned', ''),
                "work_order_id": record.get('work_order_id', ''),
                "status": record.get('status', ''),
                "chunk_id": f"wo_{record.get('work_order_id', '')}"
            }
        })
    
    return chunks


def process_inspection_reports(data: list) -> list:
    """Convert inspection reports into text chunks."""
    chunks = []
    
    for record in data:
        text = f"""
Inspection Report: {record.get('report_id', '')}
Equipment: {record.get('equipment_tag', '')}
Date: {record.get('inspection_date', '')}
Inspector: {record.get('inspector_name', '')}
Type: {record.get('inspection_type', '')}
Findings: {record.get('findings', '')}
Recommendations: {record.get('recommendations', '')}
OISD Reference: {record.get('oisd_reference', '')}
Compliance Status: {record.get('compliance_status', '')}
        """.strip()
        
        chunks.append({
            "text": text,
            "metadata": {
                "source": "inspection_reports.json",
                "doc_type": "operational",
                "record_type": "inspection_report",
                "equipment_tag": record.get('equipment_tag', ''),
                "date": record.get('inspection_date', ''),
                "inspector": record.get('inspector_name', ''),
                "compliance_status": record.get('compliance_status', ''),
                "chunk_id": f"ir_{record.get('report_id', '')}"
            }
        })
    
    return chunks


def process_incident_reports(data: list) -> list:
    """Convert incident reports into text chunks."""
    chunks = []
    
    for record in data:
        text = f"""
Incident Report: {record.get('incident_id', '')}
Date: {record.get('date', '')}
Location: {record.get('location', '')}
Type: {record.get('incident_type', '')}
Severity: {record.get('severity', '')}
Description: {record.get('description', '')}
Immediate Action: {record.get('immediate_action', '')}
Root Cause: {record.get('root_cause', '')}
Corrective Action: {record.get('corrective_action', '')}
Regulatory Reference: {record.get('regulatory_reference', '')}
Reported By: {record.get('reported_by', '')}
        """.strip()
        
        chunks.append({
            "text": text,
            "metadata": {
                "source": "incident_reports.json",
                "doc_type": "operational",
                "record_type": "incident_report",
                "severity": record.get('severity', ''),
                "incident_type": record.get('incident_type', ''),
                "date": record.get('date', ''),
                "location": record.get('location', ''),
                "chunk_id": f"inc_{record.get('incident_id', '')}"
            }
        })
    
    return chunks


def process_shift_logs(data: list) -> list:
    """Convert shift logs into text chunks."""
    chunks = []
    
    for record in data:
        text = f"""
Shift Log: {record.get('log_id', '')}
Date: {record.get('date', '')}
Shift: {record.get('shift', '')}
Supervisor: {record.get('supervisor_name', '')}
Equipment Status: {record.get('equipment_status', '')}
Production Notes: {record.get('production_notes', '')}
Pending Issues: {record.get('pending_issues', '')}
Handover Notes: {record.get('handover_notes', '')}
        """.strip()
        
        chunks.append({
            "text": text,
            "metadata": {
                "source": "shift_logs.json",
                "doc_type": "operational",
                "record_type": "shift_log",
                "date": record.get('date', ''),
                "shift": record.get('shift', ''),
                "supervisor": record.get('supervisor_name', ''),
                "chunk_id": f"sl_{record.get('log_id', '')}"
            }
        })
    
    return chunks


def process_all_json_files(generated_dir: str) -> list:
    """
    Process all JSON files in the generated data folder.
    Returns all chunks combined.
    """
    all_chunks = []
    
    # Work orders
    wo_path = os.path.join(generated_dir, "work_orders.json")
    if os.path.exists(wo_path):
        data = load_json_file(wo_path)
        chunks = process_work_orders(data)
        all_chunks.extend(chunks)
        print(f"✅ Work orders: {len(chunks)} chunks")
    
    # Inspection reports
    ir_path = os.path.join(generated_dir, "inspection_reports.json")
    if os.path.exists(ir_path):
        data = load_json_file(ir_path)
        chunks = process_inspection_reports(data)
        all_chunks.extend(chunks)
        print(f"✅ Inspection reports: {len(chunks)} chunks")
    
    # Incident reports
    inc_path = os.path.join(generated_dir, "incident_reports.json")
    if os.path.exists(inc_path):
        data = load_json_file(inc_path)
        chunks = process_incident_reports(data)
        all_chunks.extend(chunks)
        print(f"✅ Incident reports: {len(chunks)} chunks")
    
    # Shift logs
    sl_path = os.path.join(generated_dir, "shift_logs.json")
    if os.path.exists(sl_path):
        data = load_json_file(sl_path)
        chunks = process_shift_logs(data)
        all_chunks.extend(chunks)
        print(f"✅ Shift logs: {len(chunks)} chunks")
    
    return all_chunks


if __name__ == "__main__":
    from core.config import GENERATED_DIR
    
    print("Testing JSON parser...")
    chunks = process_all_json_files(GENERATED_DIR)
    print(f"\nTotal chunks from JSON files: {len(chunks)}")
    print(f"\nSample work order chunk:")
    print(chunks[0]['text'])
    print(f"\nMetadata: {chunks[0]['metadata']}")
    