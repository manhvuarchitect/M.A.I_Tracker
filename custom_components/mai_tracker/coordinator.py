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
class MedicineEvent:
    id: str
    name: str
    med_type: str
    timestamp: datetime
    reminder_time: datetime | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "med_type": self.med_type,
            "timestamp": self.timestamp.isoformat(),
            "reminder_time": self.reminder_time.isoformat() if self.reminder_time else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MedicineEvent:
        ts = datetime.fromisoformat(data["timestamp"])
        if ts.tzinfo is None: ts = ts.replace(tzinfo=UTC)
        rm = None
        if data.get("reminder_time"):
            rm = datetime.fromisoformat(data["reminder_time"])
            if rm.tzinfo is None: rm = rm.replace(tzinfo=UTC)
        return cls(
            id=data["id"],
            name=data["name"],
            med_type=data.get("med_type", "general"),
            timestamp=ts,
            reminder_time=rm,
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
    alcohol_events: list[CaffeineEvent] = field(default_factory=list)
    medicines: list[MedicineEvent] = field(default_factory=list)
    caffeine_history: list[dict[str, Any]] = field(default_factory=list)
    current_bac: float = 0.0
    drive_safe_at: datetime | None = None


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

def compute_current_bac(
    events: list[CaffeineEvent],
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
        self.weight_kg = 65.0 # Updated via options
        self.gender = "male" # Updated via options
        self._store: Store = Store(
            hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}_{entry_id}"
        )
        self._events: list[CaffeineEvent] = []
        self._alcohol_events: list[CaffeineEvent] = []
        self._medicines: list[MedicineEvent] = []
        self._caffeine_history: list[dict[str, Any]] = []
        self.water_total: float = 0.0
        self.drinks_total: dict[str, float] = {}

    async def async_load(self) -> None:
        """Load persisted events from storage."""
        stored = await self._store.async_load()
        if stored:
            if "events" in stored:
                self._events = [CaffeineEvent.from_dict(e) for e in stored["events"]]
            if "alcohol_events" in stored:
                self._alcohol_events = [CaffeineEvent.from_dict(e) for e in stored["alcohol_events"]]
            if "medicines" in stored:
                self._medicines = [MedicineEvent.from_dict(e) for e in stored["medicines"]]
            if "caffeine_history" in stored:
                self._caffeine_history = stored["caffeine_history"]
            
            today = datetime.now().strftime("%Y-%m-%d")
            if stored.get("date") == today:
                self.water_total = float(stored.get("water_total", 0.0))
                self.drinks_total = stored.get("drinks_total", {})
            else:
                # If a new day started while HA was off, push yesterday's total to history
                last_date = stored.get("date")
                last_total = float(stored.get("last_consumed_today_mg", 0.0))
                if last_date and last_total > 0:
                    self._caffeine_history.append({"date": last_date, "mg": last_total})
                    if len(self._caffeine_history) > 5:
                        self._caffeine_history.pop(0)
                self.water_total = 0.0
                self.drinks_total = {}
                
        self._prune_old_events()
        _LOGGER.debug("Loaded %d events for %s", len(self._events), self.person_name)

    async def _async_save(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        now = dt_util.utcnow()
        midnight = local_midnight_utc(now)
        today_mg = compute_consumed_today_mg(self._events, midnight)
        
        await self._store.async_save({
            "events": [e.to_dict() for e in self._events],
            "alcohol_events": [e.to_dict() for e in self._alcohol_events],
            "medicines": [e.to_dict() for e in self._medicines],
            "caffeine_history": self._caffeine_history,
            "water_total": self.water_total,
            "drinks_total": self.drinks_total,
            "date": today,
            "last_consumed_today_mg": today_mg
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
            # Auto-clear trigger
            last_date = stored.get("date")
            last_total = float(stored.get("last_consumed_today_mg", 0.0))
            if last_date and last_total > 0:
                self._caffeine_history.append({"date": last_date, "mg": last_total})
                if len(self._caffeine_history) > 5:
                    self._caffeine_history.pop(0)
            self.water_total = 0.0
            self.drinks_total = {}
            await self._async_save()

        # Compute BAC
        entry = self.hass.config_entries.async_get_entry(self.entry_id)
        if entry:
            self.weight_kg = float(entry.options.get("weight_kg", entry.data.get("weight_kg", 65.0)))
            self.gender = entry.options.get("gender", entry.data.get("gender", "male"))

        bac = compute_current_bac(self._alcohol_events, self.weight_kg, self.gender, now)
        drive_safe = compute_drive_safe_at(bac, now)

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
            alcohol_events=list(self._alcohol_events),
            medicines=list(self._medicines),
            caffeine_history=list(self._caffeine_history),
            current_bac=round(bac, 4),
            drive_safe_at=drive_safe,
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
        
        # Medicine interaction check
        now = timestamp or dt_util.utcnow()
        if cfg["caffeine_per_100ml"] > 0:
            for med in self._medicines:
                if med.med_type in ["iron", "antibiotic"] and (now - med.timestamp).total_seconds() < 7200:
                    _LOGGER.warning("Interaction alert: %s taken within 2 hours of caffeine!", med.name)
                    self.hass.components.persistent_notification.async_create(
                        f"Cảnh báo: Bạn vừa uống {med.name} cách đây chưa tới 2 tiếng. Uống Cafe/Trà bây giờ sẽ làm mất tác dụng của thuốc!",
                        title="M.A.I Tracker Cảnh báo Y tế ⚠️"
                    )

        water_delta = luong_ml * cfg["water_ratio"]
        self.water_total += water_delta
        self.drinks_total[loai] = self.drinks_total.get(loai, 0.0) + luong_ml
        
        caffeine_delta = (luong_ml / 100.0) * cfg["caffeine_per_100ml"]
        
        event_id = None
        if caffeine_delta != 0:
            event = CaffeineEvent(
                id=str(uuid.uuid4()),
                timestamp=now,
                mg=caffeine_delta,
                label=cfg["name"],
            )
            self._events.append(event)
            event_id = event.id
            _LOGGER.info("Logged %.0f mg (%s) for %s", caffeine_delta, cfg["name"], self.person_name)

        alcohol_abv = cfg.get("alcohol_abv", 0.0)
        alcohol_grams = luong_ml * alcohol_abv * 0.789
        if alcohol_grams != 0:
            event = CaffeineEvent(
                id=str(uuid.uuid4()),
                timestamp=now,
                mg=alcohol_grams,
                label=cfg["name"] + " (Alcohol)",
            )
            self._alcohol_events.append(event)

        await self._async_save()
        await self.async_refresh()
        return event_id

    async def async_log_medicine(
        self,
        name: str,
        med_type: str,
        reminder_time: datetime | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Log a medicine event."""
        now = timestamp or dt_util.utcnow()
        event = MedicineEvent(
            id=str(uuid.uuid4()),
            name=name,
            med_type=med_type,
            timestamp=now,
            reminder_time=reminder_time,
        )
        self._medicines.append(event)
        
        # Keep only the last 20 medicines
        if len(self._medicines) > 20:
            self._medicines = self._medicines[-20:]
            
        await self._async_save()
        await self.async_refresh()
        _LOGGER.info("Logged medicine %s for %s", name, self.person_name)

    async def async_set_water_total(self, value: float) -> None:
        """Manually set the total water."""
        self.water_total = value
        await self._async_save()
        await self.async_refresh()
        _LOGGER.info("Manually set water total to %.0f ml for %s", value, self.person_name)

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
        
        # Push to history before clearing
        today_mg = compute_consumed_today_mg(self._events, midnight)
        today_str = dt_util.as_local(now).strftime("%Y-%m-%d")
        if today_mg > 0:
            self._caffeine_history.append({"date": today_str, "mg": today_mg})
            if len(self._caffeine_history) > 5:
                self._caffeine_history.pop(0)
                
        self._events = [e for e in self._events if e.timestamp < midnight]
        self._alcohol_events = [e for e in self._alcohol_events if e.timestamp < midnight]
        self.water_total = 0.0
        self.drinks_total = {}
        await self._async_save()
        await self.async_refresh()
        _LOGGER.info("Cleared today's events and water for %s", self.person_name)
