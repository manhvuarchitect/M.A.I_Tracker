"""Sensor platform for Mai Drink Tracker."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    DRINK_TYPES,
    CONF_PREFIX,
    CONF_WATER_GOAL,
    SENSOR_WATER_TOTAL,
    SENSOR_CAFFEINE_TOTAL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Khởi tạo tất cả sensors cho entry này."""
    prefix = entry.data.get(CONF_PREFIX, "mai")
    water_goal = entry.data.get(CONF_WATER_GOAL, 2000)

    sensors = []

    # Sensor tổng nước quy đổi
    sensors.append(DrinkTotalSensor(hass, entry, prefix, water_goal))

    # Sensor tổng caffeine
    sensors.append(CaffeineSensor(hass, entry, prefix))

    # Sensor từng loại đồ uống
    for drink_id, cfg in DRINK_TYPES.items():
        sensors.append(DrinkTypeSensor(hass, entry, prefix, drink_id, cfg))

    async_add_entities(sensors, True)


class DrinkBaseSensor(SensorEntity):
    """Base class cho tất cả drink sensors."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, prefix: str) -> None:
        self.hass = hass
        self._entry = entry
        self._prefix = prefix
        self._unsub = None

    @property
    def _state_data(self) -> dict:
        return self.hass.data[DOMAIN][self._entry.entry_id]["data"]

    async def async_added_to_hass(self) -> None:
        """Đăng ký lắng nghe update từ service."""
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


class DrinkTotalSensor(DrinkBaseSensor):
    """Sensor tổng nước quy đổi hôm nay."""

    def __init__(self, hass, entry, prefix, water_goal) -> None:
        super().__init__(hass, entry, prefix)
        self._water_goal = water_goal
        self._attr_unique_id = f"{prefix}_{SENSOR_WATER_TOTAL}"
        self._attr_name = f"Tổng nước ({prefix})"
        self._attr_icon = "mdi:water"
        self._attr_native_unit_of_measurement = "ml"

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


class CaffeineSensor(DrinkBaseSensor):
    """Sensor tổng caffeine hôm nay."""

    def __init__(self, hass, entry, prefix) -> None:
        super().__init__(hass, entry, prefix)
        self._attr_unique_id = f"{prefix}_{SENSOR_CAFFEINE_TOTAL}"
        self._attr_name = f"Caffeine hôm nay ({prefix})"
        self._attr_icon = "mdi:coffee-to-go"
        self._attr_native_unit_of_measurement = "mg"

    @property
    def native_value(self) -> float:
        return round(self._state_data.get("caffeine_total", 0.0), 1)


class DrinkTypeSensor(DrinkBaseSensor):
    """Sensor cho từng loại đồ uống."""

    def __init__(self, hass, entry, prefix, drink_id, cfg) -> None:
        super().__init__(hass, entry, prefix)
        self._drink_id = drink_id
        self._cfg = cfg
        self._attr_unique_id = f"{prefix}_drink_{drink_id}"
        self._attr_name = f"{cfg['name']} ({prefix})"
        self._attr_icon = cfg["icon"]
        self._attr_native_unit_of_measurement = "ml"

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
