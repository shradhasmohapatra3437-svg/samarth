import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.config import DATA_DIR
from compliance.compliance_engine import run_compliance_check, get_governing_regulations
from compliance.evidence_package import generate_evidence_package

def generate_qms_report(equipment_id: str) -> dict:
    """
    Generates a structured Quality Management System (QMS) audit report for a specific equipment.
    Integrates compliance checks, evidence packaging, and regulatory checklist status.
    """
    # 1. Run compliance check query
    query = f"Check regulatory compliance and standard violations for equipment {equipment_id}"
    compliance_result = run_compliance_check(query)
    
    # 2. Get governing regulations directly from graph
    regulations = get_governing_regulations(equipment_id)
    
    # 3. Parse findings to build a structured checklist status
    answer = compliance_result.get("answer", "")
    checklist = []
    
    # Simple heuristics to map checklist status per regulation from the narrative text
    for reg in regulations:
        reg_status = "UNVERIFIED"
        details = "No regulatory text or check records available."
        
        # Check if regulation was reviewed (exists in sources)
        reg_sourced = any(reg.lower().replace("-", "_").replace(" ", "_") in src.lower().replace("-", "_").replace(" ", "_") 
                          for src in compliance_result.get("sources", []))
        
        if reg_sourced:
            reg_status = "COMPLIANT"  # default if sourced and no negative findings
            details = f"Retrieved regulatory requirements for {reg}. No violations detected."
            
            # Check for CONFIRMED violations or RISK SIGNALS in the text
            lines = answer.split("\n")
            for line in lines:
                if reg.lower() in line.lower() or reg.replace("-", " ").lower() in line.lower():
                    if "[CONFIRMED]" in line:
                        if "not met" in line.lower() or "violation" in line.lower() or "fail" in line.lower() or "non-compliant" in line.lower():
                            reg_status = "NON_COMPLIANT"
                            details = line.strip()
                        else:
                            reg_status = "COMPLIANT"
                            details = line.strip()
                    elif "[RISK_SIGNAL]" in line:
                        # Risk signal doesn't mean confirmed failure, but elevates status to WARN
                        if reg_status != "NON_COMPLIANT":
                            reg_status = "RISK_SIGNAL"
                            details = line.strip()
                            
        checklist.append({
            "regulation_id": reg,
            "status": reg_status,
            "details": details
        })
        
    # 4. Generate standard evidence package
    evidence_pkg = generate_evidence_package(compliance_result, equipment_id)
    
    # 5. Build QMS Report
    qms_report = {
        "report_type": "QMS_EQUIPMENT_AUDIT",
        "equipment_id": equipment_id,
        "generated_at": datetime.now().isoformat(),
        "overall_status": "COMPLIANT" if not any(c["status"] == "NON_COMPLIANT" for c in checklist) else "NON_COMPLIANT",
        "checklist": checklist,
        "evidence_package": evidence_pkg
    }
    
    # Save the report
    output_path = os.path.join(DATA_DIR, "processed", f"qms_report_{equipment_id}.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(qms_report, f, indent=2)
        
    print(f"[OK] QMS Audit Report saved to {output_path}")
    return qms_report

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate QMS compliance audit report for an equipment tag.")
    parser.add_argument("equipment_id", type=str, nargs="?", default="P-204", help="Equipment ID (default: P-204)")
    args = parser.parse_args()
    
    print(f"Generating QMS Report for {args.equipment_id}...")
    report = generate_qms_report(args.equipment_id)
    print(json.dumps(report, indent=2))
