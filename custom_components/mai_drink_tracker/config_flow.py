"""Config flow for Mai Drink Tracker."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from homeassistant.helpers import selector

from .const import DOMAIN, CONF_PREFIX, CONF_WATER_GOAL, CONF_NOTIFY_TARGET


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

        schema = vol.Schema({
            vol.Required(
                CONF_WATER_GOAL,
                default=self.config_entry.options.get(CONF_WATER_GOAL, self.config_entry.data.get(CONF_WATER_GOAL, 2000)),
            ): vol.All(vol.Coerce(int), vol.Range(min=500, max=5000)),
            vol.Optional(
                CONF_NOTIFY_TARGET,
                description={"suggested_value": self.config_entry.options.get(CONF_NOTIFY_TARGET, "")}
            ): selector.selector({"entity": {"domain": "notify"}}),
        })

        return self.async_show_form(step_id="init", data_schema=schema)
