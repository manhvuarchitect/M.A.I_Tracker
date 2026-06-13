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
    CONF_MEDICINE_SCHEDULE,
    CONF_WATER_REMINDER_INTERVAL,
    CONF_WATER_REMINDER_TTS,
    CONF_WATER_REMINDER_NOTIFY,
    DEFAULT_WATER_REMINDER_INTERVAL,
    DEFAULT_WATER_REMINDER_TTS,
    DEFAULT_WATER_REMINDER_NOTIFY,
    CONF_LINKED_USER,
    CONF_DRINK_LOG_NOTIFY_REMOVE,
    DEFAULT_DRINK_LOG_NOTIFY_REMOVE,
    CONF_NOTIFY_TARGET_MANAGEMENT,
    CONF_DRINK_LOG_NOTIFY_PERSONAL,
    CONF_DRINK_LOG_NOTIFY_MANAGEMENT,
    CONF_WATER_REMINDER_NOTIFY_MANAGEMENT,
    DEFAULT_DRINK_LOG_NOTIFY_PERSONAL,
    DEFAULT_DRINK_LOG_NOTIFY_MANAGEMENT,
    DEFAULT_WATER_REMINDER_NOTIFY_MANAGEMENT,
)
from .helpers import async_get_user_options


def _settings_schema(
    default_water_goal: int = 2000,
    default_half_life: float = DEFAULT_HALF_LIFE_HOURS,
    default_sleep_safe: float = DEFAULT_SLEEP_SAFE_MG,
    default_enable_absorption: bool = DEFAULT_ENABLE_ABSORPTION,
    default_absorption_time: float = DEFAULT_ABSORPTION_TIME_MIN,
    default_weight: float = DEFAULT_WEIGHT_KG,
    default_gender: str = DEFAULT_GENDER,
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
                CONF_WEIGHT_KG, default=default_weight
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
                CONF_GENDER, default=default_gender
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

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._new_name: str = ""
        self._clone_id: str = "none"
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        existing_entries = self._async_current_entries()

        if user_input is not None:
            existing_names = {
                entry.data[CONF_PERSON_NAME].lower()
                for entry in existing_entries
            }
            new_name = user_input[CONF_PERSON_NAME].strip()
            
            if new_name.lower() in existing_names:
                errors["base"] = "name_taken"
            else:
                self._new_name = new_name
                self._clone_id = user_input.get("clone_from", "none")
                self._linked_user = user_input.get(CONF_LINKED_USER, "")
                return await self.async_step_basic_settings()

        clone_options = [{"value": "none", "label": "Không sao chép (Tạo mới)"}]
        for entry in existing_entries:
            name = entry.data.get(CONF_PERSON_NAME, entry.title)
            clone_options.append({"value": entry.entry_id, "label": f"Sao chép từ: {name}"})

        user_options = await async_get_user_options(self.hass)
        user_options.insert(0, {"value": "", "label": "Không liên kết"})

        schema = {
            vol.Required(CONF_PERSON_NAME): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            ),
            vol.Optional(CONF_LINKED_USER, default=""): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=user_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        }
        
        if len(clone_options) > 1:
            schema[vol.Optional("clone_from", default="none")] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=clone_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_basic_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._data = {
                CONF_PERSON_NAME: self._new_name,
                CONF_LINKED_USER: getattr(self, "_linked_user", ""),
            }
            self._data.update(user_input)
            
            if self._clone_id != "none":
                for entry in self._async_current_entries():
                    if entry.entry_id == self._clone_id:
                        # Copy all other data and options
                        for k, v in entry.data.items():
                            if k not in self._data:
                                self._data[k] = v
                        for k, v in entry.options.items():
                            self._data[k] = v
                        break
                # If cloning, we can skip directly to creation since we have all data
                return self.async_create_entry(
                    title=self._new_name,
                    data=self._data,
                )
            
            # Go to next steps for a fresh user
            return await self.async_step_environment()

        # Pre-fill values if cloning
        def_water = 2000
        def_hl = DEFAULT_HALF_LIFE_HOURS
        def_safe = DEFAULT_SLEEP_SAFE_MG
        def_abs = DEFAULT_ENABLE_ABSORPTION
        def_abs_time = DEFAULT_ABSORPTION_TIME_MIN
        def_weight = DEFAULT_WEIGHT_KG
        def_gender = DEFAULT_GENDER

        if self._clone_id != "none":
            for entry in self._async_current_entries():
                if entry.entry_id == self._clone_id:
                    def_water = entry.data.get(CONF_WATER_GOAL, entry.options.get(CONF_WATER_GOAL, def_water))
                    def_hl = entry.data.get(CONF_HALF_LIFE_HOURS, entry.options.get(CONF_HALF_LIFE_HOURS, def_hl))
                    def_safe = entry.data.get(CONF_SLEEP_SAFE_MG, entry.options.get(CONF_SLEEP_SAFE_MG, def_safe))
                    def_abs = entry.data.get(CONF_ENABLE_ABSORPTION, entry.options.get(CONF_ENABLE_ABSORPTION, def_abs))
                    def_abs_time = entry.data.get(CONF_ABSORPTION_TIME_MIN, entry.options.get(CONF_ABSORPTION_TIME_MIN, def_abs_time))
                    def_weight = entry.data.get(CONF_WEIGHT_KG, entry.options.get(CONF_WEIGHT_KG, def_weight))
                    def_gender = entry.data.get(CONF_GENDER, entry.options.get(CONF_GENDER, def_gender))
                    break

        schema = _settings_schema(
            def_water, def_hl, def_safe, def_abs, def_abs_time, def_weight, def_gender
        ).schema

        return self.async_show_form(
            step_id="basic_settings",
            data_schema=vol.Schema(schema),
        )

    async def async_step_environment(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_notifications()

        temp_dict = {"": "Không sử dụng"}
        hum_dict = {"": "Không sử dụng"}
        
        for state in self.hass.states.async_all("sensor"):
            dc = state.attributes.get("device_class")
            if dc == "temperature":
                temp_dict[state.entity_id] = f"{state.name} ({state.entity_id})"
            elif dc == "humidity":
                hum_dict[state.entity_id] = f"{state.name} ({state.entity_id})"

        schema = {
            vol.Optional(CONF_TEMP_SENSOR, default=""): vol.In(temp_dict),
            vol.Optional(CONF_HUMIDITY_SENSOR, default=""): vol.In(hum_dict),
        }

        return self.async_show_form(
            step_id="environment",
            data_schema=vol.Schema(schema),
        )

    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_medicine()

        notify_dict = {"": "Không sử dụng"}
        for svc in self.hass.services.async_services().get("notify", {}).keys():
            notify_dict[f"notify.{svc}"] = f"notify.{svc}"

        tts_dict = {"": "Không sử dụng"}
        for state in self.hass.states.async_all("media_player"):
            tts_dict[state.entity_id] = f"{state.name} ({state.entity_id})"

        notify_options = [{"value": f"notify.{svc}", "label": f"notify.{svc}"} for svc in self.hass.services.async_services().get("notify", {}).keys()]

        schema = {
            vol.Optional(CONF_NOTIFY_TARGET, default=[]): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=notify_options,
                    multiple=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_NOTIFY_TARGET_MANAGEMENT, default=[]): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=notify_options,
                    multiple=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_TTS_TARGET, default=""): vol.In(tts_dict),
            vol.Optional(CONF_TTS_MESSAGE, default=DEFAULT_TTS_MESSAGE): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Required(CONF_WATER_REMINDER_INTERVAL, default=120): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=480, step=15,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="phút"
                )
            ),
            vol.Optional(CONF_WATER_REMINDER_TTS, default=DEFAULT_WATER_REMINDER_TTS): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Optional(CONF_WATER_REMINDER_NOTIFY, default=DEFAULT_WATER_REMINDER_NOTIFY): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Optional(CONF_WATER_REMINDER_NOTIFY_MANAGEMENT, default=DEFAULT_WATER_REMINDER_NOTIFY_MANAGEMENT): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Optional(CONF_DRINK_LOG_NOTIFY_PERSONAL, default=DEFAULT_DRINK_LOG_NOTIFY_PERSONAL): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Optional(CONF_DRINK_LOG_NOTIFY_MANAGEMENT, default=DEFAULT_DRINK_LOG_NOTIFY_MANAGEMENT): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Optional(CONF_DRINK_LOG_NOTIFY_REMOVE, default=DEFAULT_DRINK_LOG_NOTIFY_REMOVE): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
        }

        return self.async_show_form(
            step_id="notifications",
            data_schema=vol.Schema(schema),
        )

    async def async_step_medicine(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_bio_sensors()

        notify_dict = {"": "Không sử dụng"}
        for svc in self.hass.services.async_services().get("notify", {}).keys():
            notify_dict[f"notify.{svc}"] = f"notify.{svc}"

        tts_dict = {"": "Không sử dụng"}
        for state in self.hass.states.async_all("media_player"):
            tts_dict[state.entity_id] = f"{state.name} ({state.entity_id})"

        schema = {}
        for i in range(1, 11):
            schema[vol.Optional(f"medicine_{i}_name", default="")] = selector.TextSelector()
            schema[vol.Optional(f"medicine_{i}_time", default="08:00:00")] = selector.TimeSelector()
            schema[vol.Optional(f"medicine_{i}_notify", default="")] = vol.In(notify_dict)
            schema[vol.Optional(f"medicine_{i}_tts", default="")] = vol.In(tts_dict)

        return self.async_show_form(
            step_id="medicine",
            data_schema=vol.Schema(schema),
        )

    async def async_step_bio_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(
                title=self._new_name,
                data=self._data,
            )

        schema = {
            vol.Optional("heart_rate_sensors", default=[]): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True, domain="sensor")
            ),
            vol.Optional("step_sensors", default=[]): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True, domain="sensor")
            ),
            vol.Optional("weight_sensor"): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=False, domain="sensor")
            ),
        }

        return self.async_show_form(
            step_id="bio_sensors",
            data_schema=vol.Schema(schema),
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> MaiTrackerOptionsFlow:
        return MaiTrackerOptionsFlow(config_entry)


class MaiTrackerOptionsFlow(config_entries.OptionsFlow):
    """Handle options (re-configuration) for an existing entry."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__(config_entry)
        self.config_entry = config_entry
        self._options: dict[str, Any] = {}
        self._first_time = True

    def _get(self, key: str, default: Any) -> Any:
        # Trong Home Assistant, config_entry của OptionsFlow là self.config_entry
        entry = self.config_entry
        if self._first_time:
            return entry.options.get(key, entry.data.get(key, default))
        return self._options.get(key, entry.options.get(key, entry.data.get(key, default)))

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._options.update(user_input)
            self._first_time = False
            return await self.async_step_environment()

        current_water_goal = int(self._get(CONF_WATER_GOAL, 2000))
        current_half_life = float(self._get(CONF_HALF_LIFE_HOURS, DEFAULT_HALF_LIFE_HOURS))
        current_sleep_safe = float(self._get(CONF_SLEEP_SAFE_MG, DEFAULT_SLEEP_SAFE_MG))
        current_enable_absorption = bool(self._get(CONF_ENABLE_ABSORPTION, DEFAULT_ENABLE_ABSORPTION))
        current_absorption_time = float(self._get(CONF_ABSORPTION_TIME_MIN, DEFAULT_ABSORPTION_TIME_MIN))
        current_weight = float(self._get(CONF_WEIGHT_KG, DEFAULT_WEIGHT_KG))
        current_gender = str(self._get(CONF_GENDER, DEFAULT_GENDER))

        user_options = await async_get_user_options(self.hass)
        user_options.insert(0, {"value": "", "label": "Không liên kết"})
        cur_linked_user = str(self._get(CONF_LINKED_USER, ""))

        base_schema = _settings_schema(
            current_water_goal,
            current_half_life,
            current_sleep_safe,
            current_enable_absorption,
            current_absorption_time,
            current_weight,
            current_gender,
        ).schema

        schema_dict = dict(base_schema)
        schema_dict[
            vol.Optional(CONF_LINKED_USER, default=cur_linked_user)
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=user_options,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )

        schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )

    async def async_step_environment(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_notifications()

        temp_dict = {"": "Không sử dụng"}
        hum_dict = {"": "Không sử dụng"}
        
        for state in self.hass.states.async_all("sensor"):
            dc = state.attributes.get("device_class")
            if dc == "temperature":
                temp_dict[state.entity_id] = f"{state.name} ({state.entity_id})"
            elif dc == "humidity":
                hum_dict[state.entity_id] = f"{state.name} ({state.entity_id})"

        cur_temp = str(self._get(CONF_TEMP_SENSOR, ""))
        if cur_temp and cur_temp not in temp_dict: temp_dict[cur_temp] = cur_temp

        cur_hum = str(self._get(CONF_HUMIDITY_SENSOR, ""))
        if cur_hum and cur_hum not in hum_dict: hum_dict[cur_hum] = cur_hum

        schema = {
            vol.Optional(CONF_TEMP_SENSOR, default=cur_temp): vol.In(temp_dict),
            vol.Optional(CONF_HUMIDITY_SENSOR, default=cur_hum): vol.In(hum_dict),
        }

        return self.async_show_form(
            step_id="environment",
            data_schema=vol.Schema(schema),
        )

    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_medicine()

        notify_options = [{"value": f"notify.{svc}", "label": f"notify.{svc}"} for svc in self.hass.services.async_services().get("notify", {}).keys()]
            
        raw_notify = self._get(CONF_NOTIFY_TARGET, [])
        if isinstance(raw_notify, str):
            cur_notify = [raw_notify] if raw_notify else []
        else:
            cur_notify = list(raw_notify)

        cur_notify_2 = self._get("notify_target_2", "")
        cur_notify_3 = self._get("notify_target_3", "")
        if cur_notify_2 and cur_notify_2 not in cur_notify:
            cur_notify.append(cur_notify_2)
        if cur_notify_3 and cur_notify_3 not in cur_notify:
            cur_notify.append(cur_notify_3)

        tts_dict = {"": "Không sử dụng"}
        for state in self.hass.states.async_all("media_player"):
            tts_dict[state.entity_id] = f"{state.name} ({state.entity_id})"
            
        cur_tts = str(self._get(CONF_TTS_TARGET, ""))
        if cur_tts and cur_tts not in tts_dict: tts_dict[cur_tts] = cur_tts
        
        cur_msg = str(self._get(CONF_TTS_MESSAGE, DEFAULT_TTS_MESSAGE))

        cur_water_interval = int(self._get(CONF_WATER_REMINDER_INTERVAL, DEFAULT_WATER_REMINDER_INTERVAL))
        cur_water_tts = str(self._get(CONF_WATER_REMINDER_TTS, DEFAULT_WATER_REMINDER_TTS))
        cur_water_notify = str(self._get(CONF_WATER_REMINDER_NOTIFY, DEFAULT_WATER_REMINDER_NOTIFY))

        raw_notify_mgmt = self._get(CONF_NOTIFY_TARGET_MANAGEMENT, [])
        if isinstance(raw_notify_mgmt, str):
            cur_notify_mgmt = [raw_notify_mgmt] if raw_notify_mgmt else []
        else:
            cur_notify_mgmt = list(raw_notify_mgmt)

        cur_water_notify_mgmt = str(self._get(CONF_WATER_REMINDER_NOTIFY_MANAGEMENT, DEFAULT_WATER_REMINDER_NOTIFY_MANAGEMENT))
        cur_drink_log_notify_personal = str(self._get(CONF_DRINK_LOG_NOTIFY_PERSONAL, DEFAULT_DRINK_LOG_NOTIFY_PERSONAL))
        cur_drink_log_notify_mgmt = str(self._get(CONF_DRINK_LOG_NOTIFY_MANAGEMENT, DEFAULT_DRINK_LOG_NOTIFY_MANAGEMENT))
        cur_drink_log_notify_remove = str(self._get(CONF_DRINK_LOG_NOTIFY_REMOVE, DEFAULT_DRINK_LOG_NOTIFY_REMOVE))

        schema = {
            vol.Optional(CONF_NOTIFY_TARGET, default=cur_notify): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=notify_options,
                    multiple=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_NOTIFY_TARGET_MANAGEMENT, default=cur_notify_mgmt): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=notify_options,
                    multiple=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_TTS_TARGET, default=cur_tts): vol.In(tts_dict),
            vol.Optional(CONF_TTS_MESSAGE, default=cur_msg): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Required(CONF_WATER_REMINDER_INTERVAL, default=cur_water_interval): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=480, step=15,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="phút"
                )
            ),
            vol.Optional(CONF_WATER_REMINDER_TTS, default=cur_water_tts): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Optional(CONF_WATER_REMINDER_NOTIFY, default=cur_water_notify): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Optional(CONF_WATER_REMINDER_NOTIFY_MANAGEMENT, default=cur_water_notify_mgmt): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Optional(CONF_DRINK_LOG_NOTIFY_PERSONAL, default=cur_drink_log_notify_personal): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Optional(CONF_DRINK_LOG_NOTIFY_MANAGEMENT, default=cur_drink_log_notify_mgmt): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Optional(CONF_DRINK_LOG_NOTIFY_REMOVE, default=cur_drink_log_notify_remove): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
        }

        return self.async_show_form(
            step_id="notifications",
            data_schema=vol.Schema(schema),
        )

    async def async_step_medicine(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._options.update(user_input)
            
            return await self.async_step_bio_sensors()

        notify_dict = {"": "Không sử dụng"}
        for svc in self.hass.services.async_services().get("notify", {}).keys():
            notify_dict[f"notify.{svc}"] = f"notify.{svc}"

        tts_dict = {"": "Không sử dụng"}
        for state in self.hass.states.async_all("media_player"):
            tts_dict[state.entity_id] = f"{state.name} ({state.entity_id})"

        schema = {}
        for i in range(1, 11):
            cur_name = str(self._get(f"medicine_{i}_name", ""))
            cur_time = str(self._get(f"medicine_{i}_time", ""))
            if not cur_time:
                cur_time = "08:00:00"  # Default time to prevent frontend "Invalid time" error
            
            cur_notify = str(self._get(f"medicine_{i}_notify", ""))
            cur_tts = str(self._get(f"medicine_{i}_tts", ""))

            if cur_notify and cur_notify not in notify_dict: notify_dict[cur_notify] = cur_notify
            if cur_tts and cur_tts not in tts_dict: tts_dict[cur_tts] = cur_tts

            schema[vol.Optional(f"medicine_{i}_name", default=cur_name)] = selector.TextSelector()
            schema[vol.Optional(f"medicine_{i}_time", default=cur_time)] = selector.TimeSelector()
            schema[vol.Optional(f"medicine_{i}_notify", default=cur_notify)] = vol.In(notify_dict)
            schema[vol.Optional(f"medicine_{i}_tts", default=cur_tts)] = vol.In(tts_dict)

        return self.async_show_form(
            step_id="medicine",
            data_schema=vol.Schema(schema),
        )

    async def async_step_bio_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._options.update(user_input)
            
            final_options = dict(self.config_entry.options)
            final_options.update(self._options)
            if CONF_MEDICINE_SCHEDULE in final_options:
                del final_options[CONF_MEDICINE_SCHEDULE]
            return self.async_create_entry(title="", data=final_options)

        cur_hr = self._get("heart_rate_sensors", [])
        if isinstance(cur_hr, str): cur_hr = [cur_hr] if cur_hr else []
        
        cur_steps = self._get("step_sensors", [])
        if isinstance(cur_steps, str): cur_steps = [cur_steps] if cur_steps else []
        
        cur_weight = str(self._get("weight_sensor", ""))

        schema = {
            vol.Optional("heart_rate_sensors", default=cur_hr): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True, domain="sensor")
            ),
            vol.Optional("step_sensors", default=cur_steps): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True, domain="sensor")
            ),
            vol.Optional("weight_sensor"): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=False, domain="sensor")
            ),
        }
        if cur_weight:
            schema[vol.Optional("weight_sensor", default=cur_weight)] = selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=False, domain="sensor")
            )

        return self.async_show_form(
            step_id="bio_sensors",
            data_schema=vol.Schema(schema),
        )
