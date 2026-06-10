import math
from datetime import datetime, timedelta
from typing import List
from ..models import CaffeineEvent

def compute_current_mg(
    events: List[CaffeineEvent],
    half_life_hours: float,
    now: datetime,
    absorption_time_min: float = 0.0,
) -> float:
    """Exponential decay sum; with optional absorption ramp (1 - e^(-t/t_abs))."""
    hl_seconds = half_life_hours * 3600
    total = 0.0
    for event in events:
        elapsed = max(0.0, (now - event.timestamp).total_seconds())
        if absorption_time_min > 0:
            absorbed = 1.0 - math.exp(-elapsed / (absorption_time_min * 60))
        else:
            absorbed = 1.0
        total += event.mg * absorbed * (0.5 ** (elapsed / hl_seconds))
    return total

def compute_peak_mg(
    events: List[CaffeineEvent],
    half_life_hours: float,
    absorption_time_min: float,
    now: datetime,
) -> float:
    """Find the maximum caffeine level from now forward (absorption model only)."""
    peak = compute_current_mg(events, half_life_hours, now, absorption_time_min)
    for minutes in range(1, 181):
        level = compute_current_mg(
            events,
            half_life_hours,
            now + timedelta(minutes=minutes),
            absorption_time_min,
        )
        if level > peak:
            peak = level
        elif level < peak * 0.98:
            break
    return peak

def compute_sleep_safe_at(
    current_mg: float,
    half_life_hours: float,
    sleep_safe_mg: float,
    now: datetime,
) -> datetime | None:
    """Return the future datetime when level crosses threshold, or None if already safe."""
    if current_mg <= sleep_safe_mg:
        return None
    hours_needed = half_life_hours * math.log2(current_mg / sleep_safe_mg)
    return now + timedelta(hours=hours_needed)

def compute_consumed_today_mg(
    events: List[CaffeineEvent], midnight_utc: datetime
) -> float:
    """Sum of caffeine consumed since local midnight (expressed as UTC)."""
    return sum(e.mg for e in events if e.timestamp >= midnight_utc)

def compute_consumed_today_count(
    events: List[CaffeineEvent], midnight_utc: datetime
) -> int:
    """Number of caffeine events since local midnight (expressed as UTC)."""
    return sum(1 for e in events if e.timestamp >= midnight_utc)
