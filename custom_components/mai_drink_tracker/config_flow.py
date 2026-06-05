"""Config flow for Mai Drink Tracker."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from homeassistant.helpers import selector

from .const import DOMAIN, CONF_PREFIX, CONF_WATER_GOAL, CONF_NOTIFY_TARGET, CONF_TEMP_SENSOR, CONF_HUMIDITY_SENSOR


class MaiDrinkTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow: wizard cài đặt lần đầu."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Bước 1: người dùng điền thông tin cơ bản."""
        errors = {}

        if user_input is not None:
            prefix = user_input[CONF_PREFIX].strip().lower()

            # Kiểm tra prefix hợp lệ (chỉ chữ thường + số + _)
            if not prefix.replace("_", "").isalnum():
                errors[CONF_PREFIX] = "invalid_prefix"
            else:
                # Kiểm tra không trùng entry đã có
                await self.async_set_unique_id(prefix)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Drink Tracker ({prefix})",
                    data={
                        CONF_PREFIX: prefix,
                        CONF_WATER_GOAL: user_input[CONF_WATER_GOAL],
                    },
                )

        schema = vol.Schema({
            vol.Required(CONF_PREFIX, default="mai"): str,
            vol.Required(CONF_WATER_GOAL, default=2000): vol.All(
                vol.Coerce(int), vol.Range(min=500, max=5000)
            ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "prefix_example": "mai, ba, chi...",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Cho phép chỉnh sửa options sau khi đã cài."""
        return MaiDrinkTrackerOptionsFlow(config_entry)


class MaiDrinkTrackerOptionsFlow(config_entries.OptionsFlow):
    """Options flow: chỉnh sửa sau khi đã cài đặt."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        data = self.config_entry.data
        schema = {}

        # 1. Goal
        schema[vol.Required(
            CONF_WATER_GOAL,
            default=options.get(CONF_WATER_GOAL, data.get(CONF_WATER_GOAL, 2000)),
        )] = vol.All(vol.Coerce(int), vol.Range(min=500, max=5000))

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

        # Ensure current selections are in the dicts
        cur_notify = options.get(CONF_NOTIFY_TARGET, "")
        if cur_notify and cur_notify not in notify_dict:
            notify_dict[cur_notify] = cur_notify
            
        cur_temp = options.get(CONF_TEMP_SENSOR, "")
        if cur_temp and cur_temp not in temp_dict:
            temp_dict[cur_temp] = cur_temp

        cur_hum = options.get(CONF_HUMIDITY_SENSOR, "")
        if cur_hum and cur_hum not in hum_dict:
            hum_dict[cur_hum] = cur_hum

        # 3. Add to schema using vol.In
        schema[vol.Optional(CONF_NOTIFY_TARGET, default=cur_notify)] = vol.In(notify_dict)
        schema[vol.Optional(CONF_TEMP_SENSOR, default=cur_temp)] = vol.In(temp_dict)
        schema[vol.Optional(CONF_HUMIDITY_SENSOR, default=cur_hum)] = vol.In(hum_dict)

        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema))
