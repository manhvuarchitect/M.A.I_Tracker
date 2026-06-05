"""Number platform for Mai Drink Tracker.

Entity ID pattern: number.{prefix}_mvadt_{key}
Ví dụ prefix="mai":
  number.mai_mvadt_water_total
  number.mai_mvadt_cafe
  number.mai_mvadt_tra
  number.mai_mvadt_nuoc_loc
  number.mai_mvadt_sua
  number.mai_mvadt_nuoc_ep
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    DRINK_TYPES,
    CONF_PREFIX,
    CONF_WATER_GOAL,
    MVADT,
    KEY_WATER_TOTAL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    prefix = entry.data.get(CONF_PREFIX, "mai")
    water_goal = entry.data.get(CONF_WATER_GOAL, 2000)

    entities = []
    entities.append(WaterTotalNumber(hass, entry, prefix, water_goal))
    for drink_id, cfg in DRINK_TYPES.items():
        entities.append(DrinkTypeNumber(hass, entry, prefix, drink_id, cfg))

    async_add_entities(entities, True)


class DrinkBaseNumber(NumberEntity):
    _attr_should_poll = False
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 2000
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "ml"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, prefix: str) -> None:
        self.hass = hass
        self._entry = entry
        self._prefix = prefix
        self._unsub = None

    @property
    def _state_data(self) -> dict:
        return self.hass.data[DOMAIN][self._entry.entry_id]["data"]

    async def async_added_to_hass(self) -> None:
        @callback
        def _handle_update():
            self.async_write_ha_state()

        self._unsub = async_dispatcher_connect(
            self.hass,
            f"{DOMAIN}_updated_{self._entry.entry_id}",
            _handle_update,
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()

    async def async_set_native_value(self, value: float) -> None:
        """Read-only — dùng service mai_drink_tracker.log để ghi nhận."""
        pass


class WaterTotalNumber(DrinkBaseNumber):
    """number.{prefix}_mvadt_water_total"""

    def __init__(self, hass, entry, prefix, water_goal) -> None:
        super().__init__(hass, entry, prefix)
        self._water_goal = water_goal
        # Entity ID cố định: number.{prefix}_mvadt_water_total
        self._attr_unique_id = f"{prefix}_{MVADT}_{KEY_WATER_TOTAL}"
        self.entity_id = f"number.{prefix}_{MVADT}_{KEY_WATER_TOTAL}"
        self._attr_name = f"Tổng nước ({prefix})"
        self._attr_icon = "mdi:water"
        self._attr_native_max_value = water_goal

    @property
    def native_value(self) -> float:
        return round(self._state_data.get("water_total", 0.0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        d = self._state_data
        goal = self._water_goal
        total = round(d.get("water_total", 0.0))
        return {
            "goal_ml": goal,
            "percent": round(total / goal * 100) if goal > 0 else 0,
            "remaining_ml": max(goal - total, 0),
            "date": d.get("date", ""),
        }


class DrinkTypeNumber(DrinkBaseNumber):
    """number.{prefix}_mvadt_{drink_id}"""

    def __init__(self, hass, entry, prefix, drink_id, cfg) -> None:
        super().__init__(hass, entry, prefix)
        self._drink_id = drink_id
        self._cfg = cfg
        # Entity ID cố định: number.{prefix}_mvadt_{drink_id}
        self._attr_unique_id = f"{prefix}_{MVADT}_{drink_id}"
        self.entity_id = f"number.{prefix}_{MVADT}_{drink_id}"
        self._attr_name = f"{cfg['name']} ({prefix})"
        self._attr_icon = cfg["icon"]

    @property
    def native_value(self) -> float:
        return round(self._state_data["drinks"].get(self._drink_id, 0.0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        ml = self.native_value
        return {
            "caffeine_mg": round(ml / 100 * self._cfg["caffeine_per_100ml"], 1),
            "water_equivalent_ml": round(ml * self._cfg["water_ratio"]),
            "water_ratio": self._cfg["water_ratio"],
        }
