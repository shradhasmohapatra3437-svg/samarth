import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_graph.graph_query import load_graph
from rca.date_lookup import build_date_lookup, get_most_recent_date

graph = load_graph()
date_lookup = build_date_lookup()


def score_equipment_priority(equipment_id: str) -> dict:
    """
    Compute an explainable priority/risk score for an equipment item,
    based on real signals: failure frequency, recency of last failure,
    and regulatory/safety linkage. This is NOT a predicted failure date —
    it's a transparent ranking signal for maintenance planning priority.
    """
    if equipment_id not in graph.nodes:
        return {"error": f"'{equipment_id}' not found in knowledge graph."}

    edges = dict(graph[equipment_id])

    # 1. Total failure count (sum of weights for FAILED_WITH relationships)
    failure_edges = {k: v for k, v in edges.items() if v.get("relationship") == "FAILED_WITH"}
    total_failures = sum(e.get("weight", 0) for e in failure_edges.values())

    # 2. Most recent failure date, across all failure modes
    all_failure_sources = []
    for edge_data in failure_edges.values():
        all_failure_sources.extend(edge_data.get("sources", []))
    last_failure_date = get_most_recent_date(all_failure_sources, date_lookup)

    days_since_last_failure = None
    if last_failure_date:
        last_dt = datetime.strptime(last_failure_date, "%Y-%m-%d")
        days_since_last_failure = (datetime.now() - last_dt).days

    # 3. Regulatory/safety linkage
    governed_by = [k for k, v in edges.items() if v.get("relationship") == "GOVERNED_BY"]

    # 4. Simple, transparent scoring (0-10 scale) - each factor's contribution is explicit
    score = 0
    reasoning = []

    if total_failures >= 10:
        score += 4
        reasoning.append(f"High failure count ({total_failures} recorded failures)")
    elif total_failures >= 5:
        score += 2.5
        reasoning.append(f"Moderate failure count ({total_failures} recorded failures)")
    elif total_failures > 0:
        score += 1
        reasoning.append(f"Low failure count ({total_failures} recorded failures)")

    if days_since_last_failure is not None:
        if days_since_last_failure <= 30:
            score += 3
            reasoning.append(f"Recent failure ({days_since_last_failure} days ago) — may indicate unresolved issue")
        elif days_since_last_failure <= 90:
            score += 1.5
            reasoning.append(f"Failure within last 90 days ({days_since_last_failure} days ago)")
        else:
            reasoning.append(f"Last failure {days_since_last_failure} days ago")

    if governed_by:
        score += 3
        reasoning.append(f"Governed by safety regulation(s): {', '.join(governed_by)}")

    return {
        "equipment_id": equipment_id,
        "priority_score": round(min(score, 10), 1),
        "total_failures": total_failures,
        "last_failure_date": last_failure_date,
        "days_since_last_failure": days_since_last_failure,
        "governed_by": governed_by,
        "reasoning": reasoning,
        "note": "This is an explainable priority signal based on historical patterns, NOT a predicted failure date."
    }
