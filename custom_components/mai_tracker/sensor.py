"""Sensor platform for M.A.I Tracker."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.components.sensor.const import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import homeassistant.util.dt as dt_util

from .const import (
    ATTR_EVENTS,
    DOMAIN,
)
from .coordinator import CaffeineCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: CaffeineCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[_CaffeineBase] = [
        CaffeineCurrentSensor(coordinator, entry),
        CaffeineConsumedTodaySensor(coordinator, entry),
        CaffeineConsumedTodayCountSensor(coordinator, entry),
        CaffeineSleepSafeAtSensor(coordinator, entry),
    ]
    if coordinator.enable_absorption:
        entities.append(CaffeinePeakSensor(coordinator, entry))
        
    entities.append(WaterTotalSensor(coordinator, entry))
    
    temp_sensor = entry.options.get("temp_sensor", "")
    humidity_sensor = entry.options.get("humidity_sensor", "")
    if temp_sensor and humidity_sensor:
        entities.append(HeatIndexSensor(coordinator.hass, entry, temp_sensor, humidity_sensor, coordinator.person_name))

    async_add_entities(entities)


class _CaffeineBase(CoordinatorEntity[CaffeineCoordinator], SensorEntity):
    """Base entity for M.A.I Tracker sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry_id)},
            name=self.coordinator.person_name,
            manufacturer="M.A.I Tracker",
            model="Virtual Caffeine Monitor",
        )


class CaffeineCurrentSensor(_CaffeineBase):
    """Current caffeine level in the body (mg)."""

    _attr_native_unit_of_measurement = "mg"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:coffee"
    _attr_suggested_display_precision = 0
    _attr_translation_key = "current"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_current"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.current_mg if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
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
    """Total caffeine consumed since local midnight (mg)."""

    _attr_native_unit_of_measurement = "mg"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:coffee-maker"
    _attr_suggested_display_precision = 0
    _attr_translation_key = "consumed_today"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_consumed_today"

    @property
    def native_value(self) -> float | None:
        return (
            self.coordinator.data.consumed_today_mg if self.coordinator.data else None
        )


class CaffeineConsumedTodayCountSensor(_CaffeineBase):
    """Number of caffeine events since local midnight."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"
    _attr_translation_key = "consumed_today_count"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_consumed_today_count"

    @property
    def native_value(self) -> int | None:
        return (
            self.coordinator.data.consumed_today_count
            if self.coordinator.data
            else None
        )


class CaffeineSleepSafeAtSensor(_CaffeineBase):
    """Timestamp when caffeine drops below the sleep-safe threshold."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:sleep"
    _attr_translation_key = "sleep_safe_at"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_sleep_safe_at"

    @property
    def native_value(self) -> datetime | None:
        if not self.coordinator.data:
            return None
        safe_at = self.coordinator.data.sleep_safe_at
        # None means already below threshold — return now so HA shows a valid
        # timestamp and automations can compare against it (it will be in the past).
        return safe_at if safe_at is not None else dt_util.utcnow()


class CaffeinePeakSensor(_CaffeineBase):
    """Estimated peak caffeine level accounting for absorption delay."""

    _attr_native_unit_of_measurement = "mg"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:trending-up"
    _attr_suggested_display_precision = 0
    _attr_translation_key = "peak"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_peak"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.peak_mg
class WaterTotalSensor(_CaffeineBase):
    """Total water consumed today."""

    _attr_native_unit_of_measurement = "ml"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:water"
    _attr_translation_key = "water_today"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_water_today"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.water_total

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

from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.core import callback

class HeatIndexSensor(SensorEntity):
    """Cảm biến oi bức tính toán từ nhiệt độ và độ ẩm."""

    _attr_icon = "mdi:sun-thermometer"
    _attr_native_unit_of_measurement = "°C"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, temp_entity_id: str, hum_entity_id: str, person_name: str) -> None:
        self.hass = hass
        self._temp_entity_id = temp_entity_id
        self._hum_entity_id = hum_entity_id
        self._attr_unique_id = f"{entry.entry_id}_heat_index"
        self._attr_name = f"Mức độ oi bức"
        self._attr_translation_key = "heat_index"
        self._attr_native_value = None
        self._person_name = person_name
        self._entry_id = entry.entry_id

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._person_name,
            manufacturer="M.A.I Tracker",
            model="Virtual Caffeine Monitor",
        )

    async def async_added_to_hass(self):
        @callback
        def async_state_changed_listener(event):
            self.async_schedule_update_ha_state(True)
            
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._temp_entity_id, self._hum_entity_id], async_state_changed_listener
            )
        )
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        temp_state = self.hass.states.get(self._temp_entity_id)
        hum_state = self.hass.states.get(self._hum_entity_id)
        
        if temp_state and hum_state and temp_state.state not in ['unavailable', 'unknown'] and hum_state.state not in ['unavailable', 'unknown']:
            try:
                t = float(temp_state.state)
                h = float(hum_state.state)
                val = t + 0.5555 * ((6.11 * (10 ** ((7.5 * t) / (237.7 + t))) * (h / 100)) - 10)
                self._attr_native_value = round(val, 1)
            except ValueError:
                self._attr_native_value = None
        else:
            self._attr_native_value = None
