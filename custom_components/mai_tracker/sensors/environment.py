from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_state_change_event

from ..const import DOMAIN
from ..coordinator import CaffeineCoordinator

def compute_noaa_heat_index(temp_c: float, humidity: float) -> float:
    """Calculate Heat Index (Feels Like) in Celsius using NOAA/NWS standard algorithm."""
    if temp_c <= 21.0:
        return round(temp_c, 1)

    t_f = temp_c * 1.8 + 32.0
    rh = max(0.0, min(100.0, humidity))

    hi_f = 0.5 * (t_f + 61.0 + ((t_f - 68.0) * 1.2) + (rh * 0.094))

    if (hi_f + t_f) / 2.0 >= 80.0:
        hi_f = (
            -42.379
            + 2.04901523 * t_f
            + 10.14333127 * rh
            - 0.22475541 * t_f * rh
            - 0.006837663 * (t_f ** 2)
            - 0.05481717 * (rh ** 2)
            + 0.00122874 * (t_f ** 2) * rh
            + 0.00085282 * t_f * (rh ** 2)
            - 0.00000199 * (t_f ** 2) * (rh ** 2)
        )
        if rh < 13.0 and 80.0 <= t_f <= 112.0:
            adj = ((13.0 - rh) / 4.0) * ((17.0 - abs(t_f - 95.0)) / 17.0) ** 0.5
            hi_f -= adj
        elif rh > 85.0 and 80.0 <= t_f <= 87.0:
            adj = ((rh - 85.0) / 10.0) * ((87.0 - t_f) / 5.0)
            hi_f += adj

    hi_c = (hi_f - 32.0) / 1.8
    return round(max(temp_c, hi_c) if temp_c >= 26.0 else hi_c, 1)


class HeatIndexSensor(SensorEntity):
    _attr_icon = "mdi:sun-thermometer"
    _attr_native_unit_of_measurement = "°C"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, temp_entity_id: str, hum_entity_id: str, weather_entity_id: str, person_name: str) -> None:
        self.hass = hass
        self._temp_entity_id = temp_entity_id
        self._hum_entity_id = hum_entity_id
        self._weather_entity_id = weather_entity_id
        self._attr_unique_id = f"{entry.entry_id}_heat_index"
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
            
        entities_to_track = []
        if self._temp_entity_id:
            entities_to_track.append(self._temp_entity_id)
        if self._hum_entity_id:
            entities_to_track.append(self._hum_entity_id)
        if self._weather_entity_id:
            entities_to_track.append(self._weather_entity_id)

        if entities_to_track:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, entities_to_track, async_state_changed_listener
                )
            )
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        t = None
        h = None

        if self._temp_entity_id and self._hum_entity_id:
            temp_state = self.hass.states.get(self._temp_entity_id)
            hum_state = self.hass.states.get(self._hum_entity_id)
            if temp_state and hum_state and temp_state.state not in ['unavailable', 'unknown'] and hum_state.state not in ['unavailable', 'unknown']:
                try:
                    t = float(temp_state.state)
                    h = float(hum_state.state)
                except ValueError:
                    pass
        
        if (t is None or h is None) and self._weather_entity_id:
            w_state = self.hass.states.get(self._weather_entity_id)
            if w_state and w_state.state not in ['unavailable', 'unknown']:
                try:
                    t_val = w_state.attributes.get("temperature")
                    h_val = w_state.attributes.get("humidity")
                    if t_val is not None:
                        t = float(t_val)
                    if h_val is not None:
                        h = float(h_val)
                except (ValueError, TypeError):
                    pass

        if t is not None and h is not None:
            self._attr_native_value = compute_noaa_heat_index(t, h)
        else:
            self._attr_native_value = None

class DynamicWaterGoalSensor(SensorEntity):
    _attr_icon = "mdi:water-plus"
    _attr_native_unit_of_measurement = "ml"
    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator: CaffeineCoordinator) -> None:
        self.hass = hass
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_dynamic_water_goal"
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
                if hi >= 42.0:
                    bonus = 800  # Danger: Nắng nóng gay gắt
                elif hi >= 37.0:
                    bonus = 500  # Extreme Caution: Oi bức nặng mùa hè
                elif hi >= 32.0:
                    bonus = 250  # Caution: Oi nóng nhẹ
            except ValueError:
                pass
                
        new_goal = base_goal + bonus
        
        if self._attr_native_value is not None and new_goal > self._attr_native_value and bonus > 0:
            tts_target = self._entry.options.get("tts_target")
            tts_msg = self._entry.options.get("tts_message", "Nhiệt độ hôm nay rất oi bức. Mai Tracker đã tự động tăng mục tiêu nước của bạn thêm {ml} ml.")
            if tts_target:
                msg = tts_msg.replace("{ml}", str(bonus))
                self.hass.async_create_task(
                    self._coordinator._async_call_tts(tts_target, msg)
                )

        self._attr_native_value = new_goal
