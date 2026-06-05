"""M.A.I Tracker data coordinator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import logging
import math
from typing import Any
import uuid

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import homeassistant.util.dt as dt_util

from .const import (
    DEFAULT_ABSORPTION_TIME_MIN,
    DEFAULT_HALF_LIFE_HOURS,
    DEFAULT_SLEEP_SAFE_MG,
    DOMAIN,
    MAX_EVENT_AGE_MULTIPLIER,
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=1)


@dataclass
class CaffeineEvent:
    id: str
    timestamp: datetime  # UTC, timezone-aware
    mg: float
    label: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "mg": self.mg,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CaffeineEvent:
        ts = datetime.fromisoformat(data["timestamp"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        return cls(
            id=data["id"],
            timestamp=ts,
            mg=float(data["mg"]),
            label=data.get("label", "unknown"),
        )


@dataclass
class CaffeineData:
    current_mg: float
    consumed_today_mg: float
    consumed_today_count: int
    # None = already below threshold (safe now)
    sleep_safe_at: datetime | None
    # Only set when absorption model is enabled
    peak_mg: float | None = None
    events: list[CaffeineEvent] = field(default_factory=list)
    water_total: float = 0.0
    drinks_total: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Pure computation functions — easy to unit-test without HA mocks
# ---------------------------------------------------------------------------


def compute_current_mg(
    events: list[CaffeineEvent],
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
    events: list[CaffeineEvent],
    half_life_hours: float,
    absorption_time_min: float,
    now: datetime,
) -> float:
    """Find the maximum caffeine level from now forward (absorption model only).

    Scans at 1-min steps up to 3 hours; stops early once the curve is clearly declining.
    """
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
    events: list[CaffeineEvent], midnight_utc: datetime
) -> float:
    """Sum of caffeine consumed since local midnight (expressed as UTC)."""
    return sum(e.mg for e in events if e.timestamp >= midnight_utc)


def compute_consumed_today_count(
    events: list[CaffeineEvent], midnight_utc: datetime
) -> int:
    """Number of caffeine events since local midnight (expressed as UTC)."""
    return sum(1 for e in events if e.timestamp >= midnight_utc)


def local_midnight_utc(now_utc: datetime) -> datetime:
    """Return today's local midnight as a UTC datetime."""
    local_now = dt_util.as_local(now_utc)
    midnight_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return dt_util.as_utc(midnight_local)


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------


class CaffeineCoordinator(DataUpdateCoordinator[CaffeineData]):
    """Manages caffeine state for one person."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        person_name: str,
        half_life_hours: float = DEFAULT_HALF_LIFE_HOURS,
        sleep_safe_mg: float = DEFAULT_SLEEP_SAFE_MG,
        enable_absorption: bool = False,
        absorption_time_min: float = DEFAULT_ABSORPTION_TIME_MIN,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_{person_name}",
            update_interval=SCAN_INTERVAL,
        )
        self.entry_id = entry_id
        self.person_name = person_name
        self.half_life_hours = half_life_hours
        self.sleep_safe_mg = sleep_safe_mg
        self.enable_absorption = enable_absorption
        self.absorption_time_min = absorption_time_min
        self._store: Store = Store(
            hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}_{entry_id}"
        )
        self._events: list[CaffeineEvent] = []
        self.water_total: float = 0.0
        self.drinks_total: dict[str, float] = {}

    async def async_load(self) -> None:
        """Load persisted events from storage."""
        stored = await self._store.async_load()
        if stored:
            if "events" in stored:
                self._events = [CaffeineEvent.from_dict(e) for e in stored["events"]]
            
            today = datetime.now().strftime("%Y-%m-%d")
            if stored.get("date") == today:
                self.water_total = float(stored.get("water_total", 0.0))
                self.drinks_total = stored.get("drinks_total", {})
            else:
                self.water_total = 0.0
                self.drinks_total = {}
                
        self._prune_old_events()
        _LOGGER.debug("Loaded %d events for %s", len(self._events), self.person_name)

    async def _async_save(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        await self._store.async_save({
            "events": [e.to_dict() for e in self._events],
            "water_total": self.water_total,
            "drinks_total": self.drinks_total,
            "date": today
        })

    def _prune_old_events(self) -> None:
        cutoff = dt_util.utcnow() - timedelta(
            hours=MAX_EVENT_AGE_MULTIPLIER * self.half_life_hours
        )
        before = len(self._events)
        self._events = [e for e in self._events if e.timestamp > cutoff]
        pruned = before - len(self._events)
        if pruned:
            _LOGGER.debug("Pruned %d stale events for %s", pruned, self.person_name)

    async def _async_update_data(self) -> CaffeineData:
        self._prune_old_events()
        now = dt_util.utcnow()
        abs_min = self.absorption_time_min if self.enable_absorption else 0.0
        current = compute_current_mg(self._events, self.half_life_hours, now, abs_min)
        midnight = local_midnight_utc(now)
        today_mg = compute_consumed_today_mg(self._events, midnight)
        today_count = compute_consumed_today_count(self._events, midnight)

        today_str = datetime.now().strftime("%Y-%m-%d")
        stored = await self._store.async_load()
        if stored and stored.get("date") != today_str:
            self.water_total = 0.0
            self.drinks_total = {}
            await self._async_save()

        if self.enable_absorption:
            peak = compute_peak_mg(
                self._events, self.half_life_hours, self.absorption_time_min, now
            )
            # Use peak for sleep safety — level may still be rising
            safe_at = compute_sleep_safe_at(
                peak, self.half_life_hours, self.sleep_safe_mg, now
            )
        else:
            peak = None
            safe_at = compute_sleep_safe_at(
                current, self.half_life_hours, self.sleep_safe_mg, now
            )

        return CaffeineData(
            current_mg=round(current, 1),
            consumed_today_mg=round(today_mg, 1),
            consumed_today_count=today_count,
            sleep_safe_at=safe_at,
            peak_mg=round(peak, 1) if peak is not None else None,
            events=list(self._events),
            water_total=round(self.water_total, 1),
            drinks_total=dict(self.drinks_total),
        )

    # ------------------------------------------------------------------
    # Service handlers (called by sensor entity methods)
    # ------------------------------------------------------------------

    async def async_log_drink(
        self,
        loai: str,
        luong_ml: float,
        timestamp: datetime | None = None,
    ) -> str | None:
        """Log a drink, update water and add caffeine event if any."""
        from .const import DRINK_TYPES
        if loai not in DRINK_TYPES:
            _LOGGER.warning("Unknown drink type: %s", loai)
            return None
            
        cfg = DRINK_TYPES[loai]
        
        water_delta = luong_ml * cfg["water_ratio"]
        self.water_total += water_delta
        self.drinks_total[loai] = self.drinks_total.get(loai, 0.0) + luong_ml
        
        caffeine_delta = (luong_ml / 100.0) * cfg["caffeine_per_100ml"]
        
        event_id = None
        if caffeine_delta > 0:
            event = CaffeineEvent(
                id=str(uuid.uuid4()),
                timestamp=timestamp or dt_util.utcnow(),
                mg=caffeine_delta,
                label=cfg["name"],
            )
            self._events.append(event)
            event_id = event.id
            _LOGGER.info("Logged %.0f mg (%s) for %s", caffeine_delta, cfg["name"], self.person_name)

        await self._async_save()
        await self.async_refresh()
        return event_id

    async def async_remove_last(self) -> bool:
        """Remove the most recent event. Returns True if an event was removed."""
        if not self._events:
            return False
        self._events.sort(key=lambda e: e.timestamp)
        removed = self._events.pop()
        await self._async_save()
        await self.async_refresh()
        _LOGGER.info(
            "Removed last event (%s %.0f mg) for %s",
            removed.label,
            removed.mg,
            self.person_name,
        )
        return True

    async def async_remove_by_id(self, event_id: str) -> bool:
        """Remove an event by ID. Returns True if found and removed."""
        original = len(self._events)
        self._events = [e for e in self._events if e.id != event_id]
        if len(self._events) == original:
            return False
        await self._async_save()
        await self.async_refresh()
        _LOGGER.info("Removed event %s for %s", event_id, self.person_name)
        return True

    async def async_clear_today(self) -> None:
        """Remove all events from today (local time)."""
        now = dt_util.utcnow()
        midnight = local_midnight_utc(now)
        self._events = [e for e in self._events if e.timestamp < midnight]
        self.water_total = 0.0
        self.drinks_total = {}
        await self._async_save()
        await self.async_refresh()
        _LOGGER.info("Cleared today's events and water for %s", self.person_name)
