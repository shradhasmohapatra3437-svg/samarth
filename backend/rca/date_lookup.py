import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import GENERATED_DIR

PREFIX_TO_FILE = {
    "wo_": ("work_orders.json", "work_order_id"),
    "ir_": ("incident_reports.json", "incident_id"),
    "sl_": ("shift_logs.json", "log_id"),
}


def build_date_lookup() -> dict:
    """
    Build a lookup: source_id (e.g. 'wo_WO-2022-001') -> date string.
    Scans all operational JSON files once and indexes them by their
    prefixed ID, matching the same prefix convention used in graph edges.
    """
    lookup = {}

    for prefix, (filename, id_field) in PREFIX_TO_FILE.items():
        filepath = os.path.join(GENERATED_DIR, filename)
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r") as f:
            records = json.load(f)
        for record in records:
            record_id = record.get(id_field)
            date = record.get("date")
            if record_id and date:
                lookup[f"{prefix}{record_id}"] = date

    return lookup


def get_most_recent_date(source_ids: list, date_lookup: dict) -> str:
    """
    Given a list of source IDs (from a graph edge), return the most recent date.
    """
    dates = [date_lookup[sid] for sid in source_ids if sid in date_lookup]
    if not dates:
        return None
    return max(dates)  # ISO-format date strings sort correctly as strings