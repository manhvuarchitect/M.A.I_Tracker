from datetime import datetime, timedelta
from typing import List
from ..models import CaffeineEvent

def compute_current_bac(
    events: List[CaffeineEvent],
    weight_kg: float,
    gender: str,
    now: datetime
) -> float:
    """Compute Blood Alcohol Concentration (Widmark Formula)."""
    if not events: return 0.0
    r = 0.68 if gender == "male" else 0.55
    total_grams = 0.0
    
    elimination_rate_bac_per_hour = 0.015
    grams_per_hour = (elimination_rate_bac_per_hour / 100) * (weight_kg * 1000 * r)

    for event in events:
        elapsed_hours = max(0.0, (now - event.timestamp).total_seconds() / 3600.0)
        remaining = event.mg - (grams_per_hour * elapsed_hours)
        if remaining > 0:
            total_grams += remaining

    if total_grams <= 0: return 0.0
    bac = (total_grams / (weight_kg * 1000 * r)) * 100
    return max(0.0, bac)

def compute_drive_safe_at(
    current_bac: float,
    now: datetime
) -> datetime | None:
    if current_bac <= 0: return None
    hours_needed = current_bac / 0.015
    return now + timedelta(hours=hours_needed)
