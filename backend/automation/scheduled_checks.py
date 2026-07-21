import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import DATA_DIR
from knowledge_graph.graph_query import load_graph
from rca.priority_scorer import score_equipment_priority
from rca.rca_engine import run_rca
from compliance.compliance_engine import run_compliance_check
from modules.compliance.qms_report import generate_qms_report

def run_automation_audit(min_priority: float = 7.0) -> dict:
    """
    Simulates a scheduled task looping through all high-risk assets to perform compliance
    and RCA sweeps, then records persistent alerts to alerts.json.
    """
    graph = load_graph()
    equip_nodes = [node for node, data in graph.nodes(data=True) if data.get("node_type") == "equipment"]
    
    flagged_alerts = []
    
    print(f"=== Starting Scheduled Plant Asset Audit (Threshold: {min_priority}) ===")
    print(f"Found {len(equip_nodes)} equipment nodes in the plant topology.\n")
    
    for equip in sorted(equip_nodes):
        score_data = score_equipment_priority(equip)
        if "error" in score_data:
            continue
            
        score = score_data["priority_score"]
        print(f"Auditing {equip} - Priority Score: {score}/10")
        
        if score >= min_priority:
            print(f"  [FLAGGED] {equip} exceeds threshold. Launching deep audit...")
            
            # 1. Run RCA (Root Cause Analysis) with Groq call, fall back on failure
            rca_summary = "LLM RCA analysis bypassed due to rate limiting or API error."
            try:
                rca_result = run_rca(f"Run root cause analysis for {equip}")
                if rca_result and "error" not in rca_result.get("answer", "").lower():
                    rca_summary = rca_result.get("answer", "")
            except Exception as e:
                print(f"  [WARN] Groq RCA failed: {e}")
                
            # 2. Run QMS/Compliance Report, fall back on failure
            compliance_status = "UNVERIFIED"
            compliance_details = "Compliance check failed to run due to rate limiting or API error."
            
            try:
                qms_data = generate_qms_report(equip)
                compliance_status = qms_data.get("overall_status", "UNVERIFIED")
                # Summarize checklist items
                checklist_summary = []
                for item in qms_data.get("checklist", []):
                    checklist_summary.append(f"{item['regulation_id']}: {item['status']} ({item['details'][:80]}...)")
                compliance_details = "\n".join(checklist_summary)
            except Exception as e:
                print(f"  [WARN] QMS compliance audit failed: {e}")
                
            alert_entry = {
                "timestamp": datetime.now().isoformat(),
                "equipment_id": equip,
                "priority_score": score,
                "total_failures": score_data.get("total_failures", 0),
                "last_failure_date": score_data.get("last_failure_date"),
                "reasoning": score_data.get("reasoning", []),
                "governed_by": score_data.get("governed_by", []),
                "rca_summary": rca_summary,
                "compliance_status": compliance_status,
                "compliance_details": compliance_details
            }
            flagged_alerts.append(alert_entry)
            print(f"  [OK] Alert recorded for {equip}.\n")
        else:
            print(f"  [OK] Asset is within normal/moderate bounds.\n")
            
    # Persist alerts to alerts.json
    output_path = os.path.join(DATA_DIR, "processed", "alerts.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Read existing alerts to append
    existing_alerts = []
    if os.path.exists(output_path):
        try:
            with open(output_path, "r") as f:
                existing_alerts = json.load(f)
        except Exception:
            existing_alerts = []
            
    # Combine (putting newest alerts at the front)
    all_alerts = flagged_alerts + existing_alerts
    
    with open(output_path, "w") as f:
        json.dump(all_alerts, f, indent=2)
        
    print(f"=== Audit Summary ===")
    print(f"Total equipment scanned: {len(equip_nodes)}")
    print(f"Flagged assets: {len(flagged_alerts)}")
    print(f"Alerts successfully saved/appended to {output_path}")
    
    return {
        "scanned": len(equip_nodes),
        "flagged": len(flagged_alerts),
        "alerts": flagged_alerts
    }

if __name__ == "__main__":
    run_automation_audit()
