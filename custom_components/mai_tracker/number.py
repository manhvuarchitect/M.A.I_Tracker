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
    
    from .const import DRINK_TYPES
    for drink_key in DRINK_TYPES.keys():
        entities.append(DrinkTypeNumber(coordinator, entry, drink_key))
        
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
        goal = float(self._entry.options.get("water_goal", self._entry.data.get("water_goal", 2000)))
        current = self.native_value or 0.0
        return max(goal, current)

    async def async_set_native_value(self, value: float) -> None:
        current = self.native_value or 0.0
        difference = value - current
        if difference != 0:
            await self.coordinator.async_log_drink("nuoc_loc", difference)

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


class DrinkTypeNumber(CoordinatorEntity[CaffeineCoordinator], NumberEntity):
    """Sensor tracking individual drink volumes, adjustable via slider."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "ml"
    _attr_native_min_value = 0
    _attr_native_step = 50

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry, drink_key: str) -> None:
        super().__init__(coordinator)
        from .const import DRINK_TYPES
        self._entry = entry
        self._drink_key = drink_key
        
        person = coordinator.person_name.lower().replace(" ", "_")
        self.entity_id = f"number.mait_{person}_drink_{drink_key}"
        self._attr_unique_id = f"{entry.entry_id}_drink_{drink_key}_number"
        self._attr_name = DRINK_TYPES[drink_key]["name"]
        
        if "cafe" in drink_key:
            self._attr_icon = "mdi:coffee"
        elif "tra" in drink_key:
            self._attr_icon = "mdi:tea"
        elif "nuoc_ngot" in drink_key:
            self._attr_icon = "mdi:bottle-soda"
        elif "sua" in drink_key:
            self._attr_icon = "mdi:glass-mug-variant"
        elif "bia" in drink_key:
            self._attr_icon = "mdi:glass-mug"
        else:
            self._attr_icon = "mdi:cup-water"

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
        return self.coordinator.data.drinks_total.get(self._drink_key, 0.0)

    @property
    def native_max_value(self) -> float:
        current = self.native_value or 0.0
        return max(2000.0, current + 500.0)

    async def async_set_native_value(self, value: float) -> None:
        current = self.native_value or 0.0
        difference = value - current
        if difference != 0:
            await self.coordinator.async_log_drink(self._drink_key, difference)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        from .const import DRINK_TYPES
        cfg = DRINK_TYPES[self._drink_key]
        return {
            "water_ratio": cfg["water_ratio"],
            "caffeine_per_100ml": cfg["caffeine_per_100ml"],
        }
