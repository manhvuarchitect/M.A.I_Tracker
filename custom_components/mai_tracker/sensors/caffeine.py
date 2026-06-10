from datetime import datetime
from typing import Any
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
import homeassistant.util.dt as dt_util

from ..const import ATTR_EVENTS
from ..coordinator import CaffeineCoordinator
from .base import _CaffeineBase

class CaffeineCurrentSensor(_CaffeineBase):
    _attr_native_unit_of_measurement = "mg"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:coffee"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="current")
        self._attr_unique_id = f"{entry.entry_id}_current"
        self._attr_translation_key = "current"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.current_mg if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data: return {}
        return {
            ATTR_EVENTS: [
                {
                    "id": e.id,
                    "timestamp": e.timestamp.isoformat(),
                    "mg": e.mg,
                    "label": e.label,
                }
                for e in self.coordinator.data.events
            ]
        }

class CaffeineConsumedTodaySensor(_CaffeineBase):
    _attr_native_unit_of_measurement = "mg"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:coffee-maker"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="consumed_today")
        self._attr_unique_id = f"{entry.entry_id}_consumed_today"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.consumed_today_mg if self.coordinator.data else None

class CaffeinePercentSensor(_CaffeineBase):
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:percent"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="caffeine_percent")
        self._attr_unique_id = f"{entry.entry_id}_caffeine_percent"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data: return None
        return round((self.coordinator.data.consumed_today_mg / 400.0) * 100.0, 0)

class CaffeineConsumedTodayCountSensor(_CaffeineBase):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="consumed_today_count")
        self._attr_unique_id = f"{entry.entry_id}_consumed_today_count"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.consumed_today_count if self.coordinator.data else None

class CaffeineSleepSafeAtSensor(_CaffeineBase):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:sleep"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="sleep_safe_at")
        self._attr_unique_id = f"{entry.entry_id}_sleep_safe_at"

    @property
    def native_value(self) -> datetime | None:
        if not self.coordinator.data: return None
        return self.coordinator.data.sleep_safe_at if self.coordinator.data.sleep_safe_at is not None else dt_util.utcnow()

class CaffeinePeakSensor(_CaffeineBase):
    _attr_native_unit_of_measurement = "mg"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:trending-up"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="peak")
        self._attr_unique_id = f"{entry.entry_id}_peak"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data: return None
        return self.coordinator.data.peak_mg

class CaffeineCrashRiskSensor(_CaffeineBase):
    _attr_icon = "mdi:alert-circle"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="caffeine_crash_risk")
        self._attr_unique_id = f"{entry.entry_id}_caffeine_crash_risk"

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data: return "Low"
        history = self.coordinator.data.caffeine_history
        if len(history) < 3: return "Low"
        
        avg = sum(d["mg"] for d in history) / len(history)
        today = self.coordinator.data.consumed_today_mg
        now = dt_util.utcnow()
        local_now = dt_util.as_local(now)
        
        if avg > 300 and today == 0 and local_now.hour >= 10: return "High"
        if avg > 200 and today == 0 and local_now.hour >= 12: return "Medium"
        return "Low"

class CaffeineHistorySensor(_CaffeineBase):
    _attr_icon = "mdi:chart-bar"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="caffeine_history")
        self._attr_unique_id = f"{entry.entry_id}_caffeine_history"

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data: return "0"
        return str(len(self.coordinator.data.caffeine_history))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data: return {}
        return {"history": self.coordinator.data.caffeine_history}
