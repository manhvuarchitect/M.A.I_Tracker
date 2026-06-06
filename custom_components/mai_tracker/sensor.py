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
        CaffeinePercentSensor(coordinator, entry),
        BACLevelSensor(coordinator, entry),
        DriveSafeAtSensor(coordinator, entry),
        LastMedicineSensor(coordinator, entry),
        CaffeineCrashRiskSensor(coordinator, entry),
        CaffeineHistorySensor(coordinator, entry),
    ]
    if coordinator.enable_absorption:
        entities.append(CaffeinePeakSensor(coordinator, entry))
    

    temp_sensor = entry.options.get("temp_sensor", "")
    humidity_sensor = entry.options.get("humidity_sensor", "")
    if temp_sensor and humidity_sensor:
        entities.append(HeatIndexSensor(coordinator.hass, entry, temp_sensor, humidity_sensor, coordinator.person_name))
        entities.append(DynamicWaterGoalSensor(coordinator.hass, entry, coordinator))

    async_add_entities(entities)


class _CaffeineBase(CoordinatorEntity[CaffeineCoordinator], SensorEntity):
    """Base entity for M.A.I Tracker sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry, suffix: str = None) -> None:
        super().__init__(coordinator)
        self._entry = entry
        
        # Override entity_id exactly as requested
        # e.g., sensor.mait_manh_water_today
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





class CaffeineCurrentSensor(_CaffeineBase):
    """Current caffeine level in the body (mg)."""

    _attr_native_unit_of_measurement = "mg"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:coffee"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="current")
        self._attr_unique_id = f"{entry.entry_id}_current"
        self._attr_name = "Caffeine Active Level"

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

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="consumed_today")
        self._attr_unique_id = f"{entry.entry_id}_consumed_today"
        self._attr_name = "Caffeine Consumed Today"

    @property
    def native_value(self) -> float | None:
        return (
            self.coordinator.data.consumed_today_mg if self.coordinator.data else None
        )

class CaffeinePercentSensor(_CaffeineBase):
    """Percentage of FDA safe daily limit (400mg)."""

    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:percent"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="caffeine_percent")
        self._attr_unique_id = f"{entry.entry_id}_caffeine_percent"
        self._attr_name = "Caffeine Limit Percent"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        consumed = self.coordinator.data.consumed_today_mg
        # Default FDA limit is 400mg
        return round((consumed / 400.0) * 100.0, 0)


class CaffeineConsumedTodayCountSensor(_CaffeineBase):
    """Number of caffeine events since local midnight."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="consumed_today_count")
        self._attr_unique_id = f"{entry.entry_id}_consumed_today_count"
        self._attr_name = "Consumptions Today"

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

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="sleep_safe_at")
        self._attr_unique_id = f"{entry.entry_id}_sleep_safe_at"
        self._attr_name = "Sleep Safe At"

    @property
    def native_value(self) -> datetime | None:
        if not self.coordinator.data:
            return None
        safe_at = self.coordinator.data.sleep_safe_at
        return safe_at if safe_at is not None else dt_util.utcnow()


class CaffeinePeakSensor(_CaffeineBase):
    """Estimated peak caffeine level accounting for absorption delay."""

    _attr_native_unit_of_measurement = "mg"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:trending-up"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="peak")
        self._attr_unique_id = f"{entry.entry_id}_peak"
        self._attr_name = "Peak Level"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.peak_mg

class BACLevelSensor(_CaffeineBase):
    """Blood Alcohol Concentration (%)"""
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
    """When BAC reaches 0."""
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:car"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="drive_safe_at")
        self._attr_unique_id = f"{entry.entry_id}_drive_safe_at"
        self._attr_name = "Drive Safe At"

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.data.drive_safe_at if self.coordinator.data else None

class LastMedicineSensor(_CaffeineBase):
    """Last taken medicine."""
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

class CaffeineCrashRiskSensor(_CaffeineBase):
    """Risk of caffeine withdrawal."""
    _attr_icon = "mdi:alert-circle"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="caffeine_crash_risk")
        self._attr_unique_id = f"{entry.entry_id}_caffeine_crash_risk"
        self._attr_name = "Crash Risk"

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data: return "Low"
        history = self.coordinator.data.caffeine_history
        if len(history) < 3: return "Low"
        
        avg = sum(d["mg"] for d in history) / len(history)
        today = self.coordinator.data.consumed_today_mg
        now = dt_util.utcnow()
        local_now = dt_util.as_local(now)
        
        if avg > 300 and today == 0 and local_now.hour >= 10:
            return "High"
        if avg > 200 and today == 0 and local_now.hour >= 12:
            return "Medium"
        return "Low"

class CaffeineHistorySensor(_CaffeineBase):
    """Holds 5-day caffeine history."""
    _attr_icon = "mdi:chart-bar"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="caffeine_history")
        self._attr_unique_id = f"{entry.entry_id}_caffeine_history"
        self._attr_name = "Caffeine History"

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data: return "0"
        return str(len(self.coordinator.data.caffeine_history))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data: return {}
        return {"history": self.coordinator.data.caffeine_history}


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
        person = person_name.lower().replace(" ", "_")
        self.entity_id = f"sensor.mait_{person}_heat_index"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=f"M.A.I Tracker {self._person_name}",
            manufacturer="M.A.I Tracker",
            model="Assistant Tracker",
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

class DynamicWaterGoalSensor(SensorEntity):
    """Mục tiêu nước động theo Heat Index."""

    _attr_icon = "mdi:water-plus"
    _attr_native_unit_of_measurement = "ml"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator: CaffeineCoordinator) -> None:
        self.hass = hass
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_dynamic_water_goal"
        self._attr_name = f"Mục tiêu nước hôm nay"
        self._attr_translation_key = "dynamic_water_goal"
        self._attr_native_value = None
        self._person_name = coordinator.person_name
        self._entry_id = entry.entry_id
        person = self._person_name.lower().replace(" ", "_")
        self.entity_id = f"sensor.mait_{person}_dynamic_water_goal"
        self._heat_sensor_id = f"sensor.mait_{person}_heat_index"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=f"M.A.I Tracker {self._person_name}",
        )

    async def async_added_to_hass(self):
        @callback
        def async_state_changed_listener(event):
            self.async_schedule_update_ha_state(True)
            
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._heat_sensor_id], async_state_changed_listener
            )
        )
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        base_goal = float(self._entry.options.get("water_goal", self._entry.data.get("water_goal", 2000)))
        heat_state = self.hass.states.get(self._heat_sensor_id)
        
        bonus = 0
        if heat_state and heat_state.state not in ['unavailable', 'unknown']:
            try:
                hi = float(heat_state.state)
                if hi > 39: bonus = 800
                elif hi > 35: bonus = 500
                elif hi > 32: bonus = 300
            except ValueError:
                pass
                
        new_goal = base_goal + bonus
        
        # Check if goal increased, trigger TTS
        if self._attr_native_value is not None and new_goal > self._attr_native_value and bonus > 0:
            tts_target = self._entry.options.get("tts_target")
            tts_msg = self._entry.options.get("tts_message", "Nhiệt độ hôm nay rất oi bức. Mai Tracker đã tự động tăng mục tiêu nước của bạn thêm {ml} ml.")
            if tts_target:
                msg = tts_msg.replace("{ml}", str(bonus))
                self.hass.async_create_task(
                    self.hass.services.async_call("tts", "cloud_say", {
                        "entity_id": tts_target,
                        "message": msg
                    }, blocking=False)
                )

        self._attr_native_value = new_goal
