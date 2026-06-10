from datetime import datetime
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry

from ..coordinator import CaffeineCoordinator
from .base import _CaffeineBase

class BACLevelSensor(_CaffeineBase):
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:glass-wine"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="bac_level")
        self._attr_unique_id = f"{entry.entry_id}_bac_level"
        self._attr_name = "BAC Level"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.current_bac if self.coordinator.data else 0.0

class DriveSafeAtSensor(_CaffeineBase):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:car"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="drive_safe_at")
        self._attr_unique_id = f"{entry.entry_id}_drive_safe_at"
        self._attr_name = "Drive Safe At"

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.data.drive_safe_at if self.coordinator.data else None
