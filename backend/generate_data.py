import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def clean_json(raw):
    raw = raw.strip()
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            if part.startswith("json"):
                raw = part[4:].strip()
                break
            elif part.strip().startswith("[") or part.strip().startswith("{"):
                raw = part.strip()
                break
    # Find the JSON array
    start = raw.find("[")
    end = raw.rfind("]")
    if start != -1 and end != -1:
        raw = raw[start:end+1]
    return raw.strip()


def generate_with_retry(prompt, max_tokens=4000):
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=max_tokens
            )
            raw = response.choices[0].message.content
            cleaned = clean_json(raw)
            data = json.loads(cleaned)
            return data
        except json.JSONDecodeError as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt == 2:
                print("Raw response:")
                print(raw[:500])
                raise
    return []


def generate_work_orders():
    print("Generating maintenance work orders...")
    
    prompt = """Generate exactly 30 realistic maintenance work orders for SAMARTH Aluminium Plant, Angul, Odisha, India.

Equipment tags available: P-101, P-204, P-156, P-089, C-07, C-03, HX-02, CV-05, F-02
Pump P-204 must appear at least 5 times with seal failure as the failure mode.
Compressor C-07 must appear at least 3 times with vibration issues.
Technician names: Raghunath Panda, Suresh Mohanty, Bikram Nayak, Priya Sharma, Deepak Mishra
Date range: 2022-01-01 to 2026-06-30
status must be "completed" or "pending"

Return ONLY valid JSON array. No explanation. No markdown. Start with [ and end with ]

Example format:
[
  {
    "work_order_id": "WO-2022-001",
    "equipment_tag": "P-204",
    "date": "2022-03-15",
    "failure_description": "Seal failure detected",
    "technician_assigned": "Raghunath Panda",
    "resolution_notes": "Replaced mechanical seal as per OISD-STD-171",
    "oisd_reference": "OISD-STD-171",
    "downtime_hours": 8,
    "status": "completed"
  }
]"""

    return generate_with_retry(prompt, max_tokens=6000)


def generate_inspection_reports():
    print("Generating inspection reports...")
    
    prompt = """Generate exactly 20 realistic equipment inspection reports for SAMARTH Aluminium Plant, Angul, Odisha.

Equipment: P-101, P-204, C-07, HX-02, CV-05, F-02
Inspectors: Raghunath Panda, Suresh Mohanty, Priya Sharma
Date range: 2022-01-01 to 2026-06-30
compliance_status must be: "compliant", "non_compliant", or "needs_attention"

Return ONLY valid JSON array. No explanation. No markdown. Start with [ and end with ]

Example:
[
  {
    "report_id": "IR-2022-001",
    "equipment_tag": "P-204",
    "inspection_date": "2022-04-10",
    "inspector_name": "Suresh Mohanty",
    "inspection_type": "Routine",
    "findings": "Minor seal wear detected",
    "recommendations": "Schedule seal replacement within 30 days",
    "oisd_reference": "OISD-STD-137",
    "compliance_status": "needs_attention"
  }
]"""

    return generate_with_retry(prompt, max_tokens=4000)


def generate_incident_reports():
    print("Generating incident reports...")
    
    prompt = """Generate exactly 15 realistic safety incident reports for SAMARTH Aluminium Plant, Angul, Odisha.

Incident types: gas leak, equipment failure, electrical fault, slip/fall, fire near-miss
severity must be: "low", "medium", "high", or "critical"
Date range: 2022-01-01 to 2026-06-30

Return ONLY valid JSON array. No explanation. No markdown. Start with [ and end with ]

Example:
[
  {
    "incident_id": "INC-2022-001",
    "date": "2022-05-12",
    "location": "Zone 3 - Pump House",
    "incident_type": "gas leak",
    "severity": "medium",
    "description": "Minor gas leak detected near P-204",
    "immediate_action": "Area evacuated, valve closed",
    "root_cause": "Degraded seal on pump P-204",
    "corrective_action": "Seal replaced, OISD-STD-105 work permit issued",
    "regulatory_reference": "OISD-STD-105",
    "reported_by": "Raghunath Panda"
  }
]"""

    return generate_with_retry(prompt, max_tokens=3000)


def generate_shift_logs():
    print("Generating shift logs...")
    
    prompt = """Generate exactly 15 realistic shift handover logs for SAMARTH Aluminium Plant, Angul, Odisha.

Shifts: Morning (6am-2pm), Afternoon (2pm-10pm), Night (10pm-6am)
Date range: 2024-01-01 to 2026-06-30
Mix Hindi and English naturally.

Return ONLY valid JSON array. No explanation. No markdown. Start with [ and end with ]

Example:
[
  {
    "log_id": "SL-2024-001",
    "date": "2024-01-15",
    "shift": "Morning",
    "supervisor_name": "Bikram Nayak",
    "equipment_status": "P-204 running normal, C-07 under observation",
    "production_notes": "Target 95% achieved. Furnace F-02 temperature stable.",
    "pending_issues": "CV-05 belt tension check pending",
    "handover_notes": "Raat mein C-07 ki vibration thodi zyada thi, monitor karte rehna"
  }
]"""

    return generate_with_retry(prompt, max_tokens=2000)


def save_data(data, filename):
    filepath = f"../data/generated/{filename}"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved {len(data)} records to {filepath}")


def main():
    print("=" * 50)
    print("SAMARTH Data Generator")
    print("=" * 50)

    work_orders = generate_work_orders()
    save_data(work_orders, "work_orders.json")

    inspection_reports = generate_inspection_reports()
    save_data(inspection_reports, "inspection_reports.json")

    incident_reports = generate_incident_reports()
    save_data(incident_reports, "incident_reports.json")

    shift_logs = generate_shift_logs()
    save_data(shift_logs, "shift_logs.json")

    print("=" * 50)
    print("✅ All data generated successfully")
    print("📁 Check data/generated/ folder")
    print("=" * 50)


if __name__ == "__main__":
    main()
    