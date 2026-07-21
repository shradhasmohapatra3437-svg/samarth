import random


def get_simulated_conditions(equipment_id: str) -> dict:
    """
    SIMULATED real-time operating conditions for a given equipment ID.
    This is NOT live sensor data — no IoT/SCADA integration exists in this project.
    This function generates plausible current readings to demonstrate how the
    RCA agent would incorporate real-time conditions if connected to actual
    plant telemetry in a production deployment.
    """
    random.seed(hash(equipment_id) % 1000)  # consistent per equipment, not random each call

    return {
        "equipment_id": equipment_id,
        "temperature_c": round(random.uniform(45, 85), 1),
        "vibration_mm_s": round(random.uniform(1.5, 9.0), 2),
        "pressure_bar": round(random.uniform(4.0, 12.0), 1),
        "is_simulated": True,
        "note": "Simulated reading — no live sensor/SCADA integration in this deployment."
    }
