"""Config flow for M.A.I Tracker."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.helpers import selector
import voluptuous as vol

from .const import (
    CONF_ABSORPTION_TIME_MIN,
    CONF_ENABLE_ABSORPTION,
    CONF_HALF_LIFE_HOURS,
    CONF_PERSON_NAME,
    CONF_SLEEP_SAFE_MG,
    CONF_WATER_GOAL,
    CONF_NOTIFY_TARGET,
    CONF_TEMP_SENSOR,
    CONF_HUMIDITY_SENSOR,
    DEFAULT_ABSORPTION_TIME_MIN,
    DEFAULT_ENABLE_ABSORPTION,
    DEFAULT_HALF_LIFE_HOURS,
    DEFAULT_SLEEP_SAFE_MG,
    DOMAIN,
    MAX_ABSORPTION_TIME_MIN,
    MAX_HALF_LIFE_HOURS,
    MIN_ABSORPTION_TIME_MIN,
    MIN_HALF_LIFE_HOURS,
    CONF_WEIGHT_KG,
    CONF_GENDER,
    CONF_TTS_TARGET,
    CONF_TTS_MESSAGE,
    DEFAULT_WEIGHT_KG,
    DEFAULT_GENDER,
    DEFAULT_TTS_MESSAGE,
)


def _settings_schema(
    default_water_goal: int = 2000,
    default_half_life: float = DEFAULT_HALF_LIFE_HOURS,
    default_sleep_safe: float = DEFAULT_SLEEP_SAFE_MG,
    default_enable_absorption: bool = DEFAULT_ENABLE_ABSORPTION,
    default_absorption_time: float = DEFAULT_ABSORPTION_TIME_MIN,
) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_WATER_GOAL, default=default_water_goal
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=500, max=5000, step=100,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="ml",
                )
            ),
            vol.Required(
                CONF_HALF_LIFE_HOURS, default=default_half_life
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_HALF_LIFE_HOURS,
                    max=MAX_HALF_LIFE_HOURS,
                    step=0.5,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="h",
                )
            ),
            vol.Required(
                CONF_SLEEP_SAFE_MG, default=default_sleep_safe
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=500,
                    step=5,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="mg",
                )
            ),
            vol.Required(
                CONF_ENABLE_ABSORPTION, default=default_enable_absorption
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_ABSORPTION_TIME_MIN, default=default_absorption_time
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_ABSORPTION_TIME_MIN,
                    max=MAX_ABSORPTION_TIME_MIN,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="min",
                )
            ),
            vol.Required(
                CONF_WEIGHT_KG, default=DEFAULT_WEIGHT_KG
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=30.0,
                    max=200.0,
                    step=0.5,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="kg",
                )
            ),
            vol.Required(
                CONF_GENDER, default=DEFAULT_GENDER
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": "male", "label": "Nam"},
                        {"value": "female", "label": "Nữ"}
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


class MaiTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for M.A.I Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            existing_names = {
                entry.data[CONF_PERSON_NAME].lower()
                for entry in self._async_current_entries()
            }
            if user_input[CONF_PERSON_NAME].lower() in existing_names:
                errors["base"] = "name_taken"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_PERSON_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PERSON_NAME): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                }
            ).extend(_settings_schema(default_water_goal=2000).schema),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> MaiTrackerOptionsFlow:
        return MaiTrackerOptionsFlow()


class MaiTrackerOptionsFlow(config_entries.OptionsFlow):
    """Handle options (re-configuration) for an existing entry."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        def _get(key: str, default: float | bool | int | str) -> Any:
            return self.config_entry.options.get(
                key, self.config_entry.data.get(key, default)
            )

        current_water_goal = int(_get(CONF_WATER_GOAL, 2000))
        current_half_life = float(_get(CONF_HALF_LIFE_HOURS, DEFAULT_HALF_LIFE_HOURS))
        current_sleep_safe = float(_get(CONF_SLEEP_SAFE_MG, DEFAULT_SLEEP_SAFE_MG))
        current_enable_absorption = bool(
            _get(CONF_ENABLE_ABSORPTION, DEFAULT_ENABLE_ABSORPTION)
        )
        current_absorption_time = float(
            _get(CONF_ABSORPTION_TIME_MIN, DEFAULT_ABSORPTION_TIME_MIN)
        )

        schema = _settings_schema(
            current_water_goal,
            current_half_life,
            current_sleep_safe,
            current_enable_absorption,
            current_absorption_time,
        ).schema

        # 2. Build dynamic dicts for dropdowns
        notify_dict = {"": "Không sử dụng"}
        for svc in self.hass.services.async_services().get("notify", {}).keys():
            notify_dict[f"notify.{svc}"] = f"notify.{svc}"

        temp_dict = {"": "Không sử dụng"}
        hum_dict = {"": "Không sử dụng"}
        
        for state in self.hass.states.async_all("sensor"):
            dc = state.attributes.get("device_class")
            if dc == "temperature":
                temp_dict[state.entity_id] = f"{state.name} ({state.entity_id})"
            elif dc == "humidity":
                hum_dict[state.entity_id] = f"{state.name} ({state.entity_id})"

        cur_notify = str(_get(CONF_NOTIFY_TARGET, ""))
        if cur_notify and cur_notify not in notify_dict:
            notify_dict[cur_notify] = cur_notify
            
        cur_temp = str(_get(CONF_TEMP_SENSOR, ""))
        if cur_temp and cur_temp not in temp_dict:
            temp_dict[cur_temp] = cur_temp

        cur_hum = str(_get(CONF_HUMIDITY_SENSOR, ""))
        if cur_hum and cur_hum not in hum_dict:
            hum_dict[cur_hum] = cur_hum

        schema[vol.Optional(CONF_NOTIFY_TARGET, default=cur_notify)] = vol.In(notify_dict)
        schema[vol.Optional(CONF_TEMP_SENSOR, default=cur_temp)] = vol.In(temp_dict)
        schema[vol.Optional(CONF_HUMIDITY_SENSOR, default=cur_hum)] = vol.In(hum_dict)

        # 3. Build dynamic dicts for TTS Media Players
        tts_dict = {"": "Không sử dụng"}
        for state in self.hass.states.async_all("media_player"):
            tts_dict[state.entity_id] = f"{state.name} ({state.entity_id})"
            
        cur_tts = str(_get(CONF_TTS_TARGET, ""))
        if cur_tts and cur_tts not in tts_dict:
            tts_dict[cur_tts] = cur_tts
            
        schema[vol.Optional(CONF_TTS_TARGET, default=cur_tts)] = vol.In(tts_dict)
        schema[vol.Optional(CONF_TTS_MESSAGE, default=str(_get(CONF_TTS_MESSAGE, DEFAULT_TTS_MESSAGE)))] = selector.TextSelector(
            selector.TextSelectorConfig(multiline=True)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )
