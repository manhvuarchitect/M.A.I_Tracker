from typing import Any
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from ..const import DOMAIN
from ..coordinator import CaffeineCoordinator

class _CaffeineBase(CoordinatorEntity[CaffeineCoordinator], SensorEntity):
    "_attr_has_entity_name = True

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry, suffix: str = None) -> None:
        super().__init__(coordinator)
        self._entry = entry
        if suffix:
            person = coordinator.person_name.lower().replace(" ", "_")
            self.entity_id = f"sensor.mait_{person}_{suffix}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry_id)},
            name=f"M.A.I Tracker {self.coordinator.person_name}",
            manufacturer="M.A.I Tracker",
            model="Assistant Tracker",
        )

