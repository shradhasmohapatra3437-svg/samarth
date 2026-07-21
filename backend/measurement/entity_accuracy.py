import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import GENERATED_DIR
from knowledge_graph.graph_query import load_graph

graph = load_graph()


def check_records(filename, checks):
    """
    checks: list of (field_name, label) tuples to verify against graph nodes.
    Only checks fields that actually exist and have a non-empty value.
    """
    filepath = os.path.join(GENERATED_DIR, filename)
    with open(filepath, "r") as f:
        records = json.load(f)

    total_checks = 0
    correct_checks = 0
    missed_examples = []

    for record in records:
        record_id = record.get(list(record.keys())[0], "unknown")
        for field_name, label in checks:
            value = record.get(field_name)
            if value:
                total_checks += 1
                if value in graph.nodes:
                    correct_checks += 1
                else:
                    missed_examples.append(f"{label} '{value}' from {record_id} not in graph")

    accuracy = round((correct_checks / total_checks) * 100, 1) if total_checks else 0
    return {
        "source": filename,
        "total_checks": total_checks,
        "correct": correct_checks,
        "accuracy_pct": accuracy,
        "missed_examples": missed_examples[:5]
    }


def check_work_orders_accuracy():
    return check_records("work_orders.json", [
        ("equipment_tag", "Equipment"),
        ("technician_assigned", "Technician"),
    ])


def check_inspection_reports_accuracy():
    return check_records("inspection_reports.json", [
        ("equipment_tag", "Equipment"),
        ("inspector_name", "Inspector"),
    ])


def check_incident_reports_accuracy():
    # NOTE: incident_reports.json has no direct equipment_tag field —
    # only 'location' and 'reported_by'. We check what actually exists,
    # not force a field that isn't there.
    return check_records("incident_reports.json", [
        ("location", "Location"),
        ("reported_by", "Reporter"),
    ])


def check_shift_logs_accuracy():
    # NOTE: shift_logs.json has 'supervisor_name' as a clean field,
    # but 'equipment_status' is free text (e.g. "P-204 running normal"),
    # not a clean tag — so we CANNOT directly check it against graph nodes
    # the same way. Only supervisor_name is checkable this way.
    return check_records("shift_logs.json", [
        ("supervisor_name", "Supervisor"),
    ])


if __name__ == "__main__":
    results = [
        check_work_orders_accuracy(),
        check_inspection_reports_accuracy(),
        check_incident_reports_accuracy(),
        check_shift_logs_accuracy(),
    ]
    for r in results:
        print(json.dumps(r, indent=2))
        print()

    total_checks = sum(r["total_checks"] for r in results)
    total_correct = sum(r["correct"] for r in results)
    overall = round((total_correct / total_checks) * 100, 1) if total_checks else 0
    print(f"OVERALL ACCURACY ACROSS ALL 4 DOCUMENT TYPES: {overall}% ({total_correct}/{total_checks})")
    