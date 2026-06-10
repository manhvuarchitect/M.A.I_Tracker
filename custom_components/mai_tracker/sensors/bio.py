from typing import Any
from homeassistant.components.sensor.const import SensorStateClass
from homeassistant.config_entries import ConfigEntry

from ..coordinator import CaffeineCoordinator
from .base import _CaffeineBase

class LastMedicineSensor(_CaffeineBase):
    _attr_icon = "mdi:pill"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="last_medicine")
        self._attr_unique_id = f"{entry.entry_id}_last_medicine"
        self._attr_name = "Last Medicine"

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data or not self.coordinator.data.medicines:
            return "None"
        last = self.coordinator.data.medicines[-1]
        return last.name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data or not self.coordinator.data.medicines:
            return {}
        last = self.coordinator.data.medicines[-1]
        return {
            "type": last.med_type,
            "timestamp": last.timestamp.isoformat(),
            "reminder_time": last.reminder_time.isoformat() if last.reminder_time else None
        }

class AggregatedHeartRateSensor(_CaffeineBase):
    _attr_icon = "mdi:heart-pulse"
    _attr_native_unit_of_measurement = "bpm"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="aggregated_heart_rate")
        self._attr_unique_id = f"{entry.entry_id}_aggregated_heart_rate"
        self._attr_name = "Aggregated Heart Rate"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.aggregated_heart_rate if self.coordinator.data else None

class AggregatedStepsSensor(_CaffeineBase):
    _attr_icon = "mdi:shoe-print"
    _attr_native_unit_of_measurement = "steps"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="aggregated_steps")
        self._attr_unique_id = f"{entry.entry_id}_aggregated_steps"
        self._attr_name = "Aggregated Steps"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.aggregated_steps if self.coordinator.data else None
