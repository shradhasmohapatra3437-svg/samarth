import os
import sys
import json
import networkx as nx
from collections import Counter
from groq import Groq

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.config import GROQ_API_KEY, GROQ_MODEL, DATA_DIR
from knowledge_graph.graph_query import load_graph
from rca.priority_scorer import score_equipment_priority

client = Groq(api_key=GROQ_API_KEY)

def generate_fleet_report() -> dict:
    """
    Analyzes the entire knowledge graph to identify fleet-wide patterns:
    1. Top 5 highest priority/risk equipment.
    2. Overall most common failure modes.
    3. Repeat offenders (equipment failing in the same mode >= 3 times).
    4. Technician workload and specialization mapping.
    Generates a structured report and calls Groq to write an executive summary.
    """
    graph = load_graph()
    
    # 1. Calculate priority scores for all equipment
    equipment_scores = []
    for node, data in graph.nodes(data=True):
        if data.get("node_type") == "equipment":
            score_data = score_equipment_priority(node)
            if "error" not in score_data:
                equipment_scores.append({
                    "equipment_id": node,
                    "priority_score": score_data["priority_score"],
                    "total_failures": score_data["total_failures"],
                    "governed_by": score_data["governed_by"],
                    "reasoning": score_data["reasoning"]
                })
    
    # Sort by priority score descending, then by total failures descending
    equipment_scores.sort(key=lambda x: (x["priority_score"], x["total_failures"]), reverse=True)
    top_5_risk = equipment_scores[:5]
    
    # 2. Most common failure modes in the fleet
    failure_counts = Counter()
    repeat_offenders = []
    
    # 3. Workload / Technician mapping
    tech_repairs = Counter()
    equip_techs = {} # equip -> list of techs
    
    for u, v, data in graph.edges(data=True):
        rel = data.get("relationship")
        weight = data.get("weight", 1)
        
        if rel == "FAILED_WITH":
            # u is equipment, v is failure_mode
            failure_counts[v] += weight
            if weight >= 3:
                repeat_offenders.append({
                    "equipment_id": u,
                    "failure_mode": v,
                    "occurrences": weight
                })
        elif rel == "REPAIRED_BY":
            # u is equipment, v is person (technician)
            tech_repairs[v] += weight
            if u not in equip_techs:
                equip_techs[u] = []
            equip_techs[u].append({"name": v, "repairs": weight})
            
    # Format top failure modes
    most_common_failures = [{"failure_mode": k, "count": v} for k, v in failure_counts.most_common(5)]
    
    # Format technician stats
    technician_workload = [{"name": k, "total_repairs": v} for k, v in tech_repairs.most_common()]
    
    # Construct the raw data dict
    report_data = {
        "top_risk_equipment": top_5_risk,
        "most_common_failures": most_common_failures,
        "repeat_offenders": repeat_offenders,
        "technician_workload": technician_workload,
        "equipment_to_technician_map": equip_techs
    }
    
    # Generate executive summary narrative via Groq
    prompt = f"""You are a Lead Maintenance Architect and Reliability Engineer.
Analyze the following fleet-level industrial maintenance data and write a concise, highly professional executive summary.

FLEET REPORT DATA:
{json.dumps(report_data, indent=2)}

Include the following sections in your summary:
1. FLEET HEALTH OVERVIEW - Summarize overall status and identify the most critical risk areas.
2. SYSTEMIC FAILURE PATTERNS - Discuss the most common failure modes and what they indicate (e.g. lubrication issues, seal failures).
3. KEY RECOMMENDATIONS - Provide 3-4 specific, actionable reliability improvements (e.g. preventive maintenance intervals, training, spares optimization).

Use factual, engineering-oriented language. Be concise and keep it under 500 words."""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a reliability engineering expert who writes concise executive summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=600
        )
        executive_summary = response.choices[0].message.content.strip()
    except Exception as e:
        executive_summary = f"Error generating executive summary: {e}"
        
    report_data["executive_summary"] = executive_summary
    
    # Save the report
    output_path = os.path.join(DATA_DIR, "processed", "fleet_failure_report.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report_data, f, indent=2)
    print(f"[OK] Fleet failure report saved to {output_path}")
    
    return report_data

if __name__ == "__main__":
    print("Running Fleet Failure Intelligence analysis...")
    report = generate_fleet_report()
    print("\n--- EXECUTIVE SUMMARY ---")
    print(report["executive_summary"])
