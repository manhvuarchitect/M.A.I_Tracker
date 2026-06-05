"""Number platform for M.A.I Tracker."""

from __future__ import annotations
from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CaffeineCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up M.A.I Tracker number entities."""
    coordinator: CaffeineCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [WaterTotalNumber(coordinator, entry)]
    async_add_entities(entities)


class WaterTotalNumber(CoordinatorEntity[CaffeineCoordinator], NumberEntity):
    """Total water consumed today as a slider."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "ml"
    _attr_icon = "mdi:water"
    _attr_translation_key = "water_today"
    _attr_native_min_value = 0
    _attr_native_step = 50

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        
        person = coordinator.person_name.lower().replace(" ", "_")
        self.entity_id = f"number.mait_{person}_water_today"
        self._attr_unique_id = f"{entry.entry_id}_water_today_number"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry_id)},
            name=f"M.A.I Tracker {self.coordinator.person_name}",
            manufacturer="M.A.I Tracker",
            model="Assistant Tracker",
        )

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.water_total

    @property
    def native_max_value(self) -> float:
        """Return the maximum value (the daily water goal)."""
        goal = float(self._entry.options.get("water_goal", self._entry.data.get("water_goal", 2000)))
        # allow overriding beyond goal if currently above
        current = self.native_value or 0.0
        return max(goal, current)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        await self.coordinator.async_set_water_total(value)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        goal = float(self._entry.options.get("water_goal", self._entry.data.get("water_goal", 2000)))
        total = self.coordinator.data.water_total
        return {
            "goal_ml": goal,
            "percent": round(total / goal * 100) if goal > 0 else 0,
            "remaining_ml": max(goal - total, 0),
        }
