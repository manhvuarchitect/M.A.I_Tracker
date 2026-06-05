"""Sensor platform for Mai Drink Tracker.

Entity ID pattern: sensor.{prefix}_mvadt_{key}
Ví dụ prefix="mai":
  sensor.mai_mvadt_caffeine
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN,
    DRINK_TYPES,
    CONF_PREFIX,
    CONF_WATER_GOAL,
    CONF_TEMP_SENSOR,
    CONF_HUMIDITY_SENSOR,
    MVADT,
    KEY_WATER_TOTAL,
    KEY_CAFFEINE_TOTAL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    prefix = entry.data.get(CONF_PREFIX, "mai")
    water_goal = entry.options.get(CONF_WATER_GOAL, entry.data.get(CONF_WATER_GOAL, 2000))

    sensors = []
    sensors.append(WaterTotalSensor(hass, entry, prefix, water_goal))
    sensors.append(CaffeineSensor(hass, entry, prefix))

    temp_sensor = entry.options.get(CONF_TEMP_SENSOR, "")
    humidity_sensor = entry.options.get(CONF_HUMIDITY_SENSOR, "")

    if temp_sensor and humidity_sensor:
        sensors.append(HeatIndexSensor(hass, entry, prefix, temp_sensor, humidity_sensor))

    async_add_entities(sensors, True)


class DrinkBaseSensor(SensorEntity):
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


class WaterTotalSensor(DrinkBaseSensor):
    """sensor.{prefix}_mvadt_water_total — backup cho number entity."""

    def __init__(self, hass, entry, prefix, water_goal) -> None:
        super().__init__(hass, entry, prefix)
        self._water_goal = water_goal
        self._attr_unique_id = f"{prefix}_{MVADT}_{KEY_WATER_TOTAL}_sensor"
        self.entity_id = f"sensor.{prefix}_{MVADT}_{KEY_WATER_TOTAL}"
        self._attr_name = f"Tổng nước sensor ({prefix})"
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
    """sensor.{prefix}_mvadt_caffeine"""

    def __init__(self, hass, entry, prefix) -> None:
        super().__init__(hass, entry, prefix)
        self._attr_unique_id = f"{prefix}_{MVADT}_{KEY_CAFFEINE_TOTAL}"
        self.entity_id = f"sensor.{prefix}_{MVADT}_caffeine"
        self._attr_name = f"Caffeine hôm nay ({prefix})"
        self._attr_icon = "mdi:coffee-to-go"
        self._attr_native_unit_of_measurement = "mg"

    @property
    def native_value(self) -> float:
        return round(self._state_data.get("caffeine_total", 0.0), 1)


class HeatIndexSensor(SensorEntity):
    """Cảm biến oi bức tính toán từ nhiệt độ và độ ẩm."""

    _attr_icon = "mdi:sun-thermometer"
    _attr_native_unit_of_measurement = "°C"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, prefix: str, temp_entity_id: str, hum_entity_id: str) -> None:
        self.hass = hass
        self._temp_entity_id = temp_entity_id
        self._hum_entity_id = hum_entity_id
        self._attr_unique_id = f"{prefix}_heat_index_sensor"
        self.entity_id = f"sensor.muc_do_oi_buc_{prefix}"
        self._attr_name = f"Mức độ oi bức ({prefix})"
        self._attr_native_value = None

    async def async_added_to_hass(self):
        @callback
        def async_state_changed_listener(event):
            self.async_schedule_update_ha_state(True)
            
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._temp_entity_id, self._hum_entity_id], async_state_changed_listener
            )
        )
        # Update once on startup
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        temp_state = self.hass.states.get(self._temp_entity_id)
        hum_state = self.hass.states.get(self._hum_entity_id)
        
        if temp_state and hum_state and temp_state.state not in ['unavailable', 'unknown'] and hum_state.state not in ['unavailable', 'unknown']:
            try:
                t = float(temp_state.state)
                h = float(hum_state.state)
                # T + 0.5555 * ((6.11 * (10 ** ((7.5 * T) / (237.7 + T))) * (H / 100)) - 10)
                val = t + 0.5555 * ((6.11 * (10 ** ((7.5 * t) / (237.7 + t))) * (h / 100)) - 10)
                self._attr_native_value = round(val, 1)
            except ValueError:
                self._attr_native_value = None
        else:
            self._attr_native_value = None
