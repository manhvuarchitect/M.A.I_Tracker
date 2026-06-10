from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_state_change_event

from ..const import DOMAIN
from ..coordinator import CaffeineCoordinator

class HeatIndexSensor(SensorEntity):
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
        self._attr_name = "Mức độ oi bức"
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
        self._attr_name = "Mục tiêu nước hôm nay"
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
