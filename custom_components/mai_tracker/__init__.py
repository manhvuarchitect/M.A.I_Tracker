"""The M.A.I Tracker integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, service
import homeassistant.util.dt as dt_util
import voluptuous as vol
from datetime import datetime

from .const import (
    ATTR_EVENT_ID,
    ATTR_LABEL,
    ATTR_MG,
    ATTR_TIMESTAMP,
    CONF_ABSORPTION_TIME_MIN,
    CONF_ENABLE_ABSORPTION,
    CONF_HALF_LIFE_HOURS,
    CONF_PERSON_NAME,
    CONF_SLEEP_SAFE_MG,
    DEFAULT_ABSORPTION_TIME_MIN,
    DEFAULT_ENABLE_ABSORPTION,
    DEFAULT_HALF_LIFE_HOURS,
    DEFAULT_SLEEP_SAFE_MG,
    DOMAIN,
    SERVICE_CLEAR_TODAY,
    SERVICE_LOG_CONSUMPTION,
    SERVICE_REMOVE_BY_ID,
    SERVICE_REMOVE_LAST,
    CONF_DRINK_LOG_NOTIFY_REMOVE,
    DEFAULT_DRINK_LOG_NOTIFY_REMOVE,
    CONF_NOTIFY_TARGET_MANAGEMENT,
    CONF_DRINK_LOG_NOTIFY_PERSONAL,
    CONF_DRINK_LOG_NOTIFY_MANAGEMENT,
    DEFAULT_DRINK_LOG_NOTIFY_PERSONAL,
    DEFAULT_DRINK_LOG_NOTIFY_MANAGEMENT,
)
from .coordinator import CaffeineCoordinator
from .helpers import resolve_entry_id_by_user_id

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.NUMBER]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the M.A.I Tracker integration."""

    async def handle_service(call: ServiceCall) -> None:
        """Handle the service call."""
        entry_ids = await service.async_extract_config_entry_ids(hass, call)  # type: ignore[call-arg]

        if not entry_ids:
            user_id = call.context.user_id
            resolved_entry_id = resolve_entry_id_by_user_id(hass, user_id)
            if resolved_entry_id:
                entry_ids = {resolved_entry_id}
            else:
                entry_ids = set(hass.data.get(DOMAIN, {}).keys())

        for entry_id in entry_ids:
            if entry_id not in hass.data.get(DOMAIN, {}):
                continue
            coordinator: CaffeineCoordinator = hass.data[DOMAIN][entry_id]

            if call.service == "log_drink":
                loai = call.data["loai"]
                luong_ml = call.data["luong_ml"]
                timestamp_str = call.data.get(ATTR_TIMESTAMP)
                ts = None
                if timestamp_str:
                    ts = dt_util.parse_datetime(timestamp_str)
                    if ts and ts.tzinfo is None:
                        ts = dt_util.as_utc(ts)

                await coordinator.async_log_drink(
                    loai=loai, luong_ml=luong_ml, timestamp=ts
                )
                
                # Check notification
                entry_obj = hass.config_entries.async_get_entry(entry_id)
                entry_options = entry_obj.options if entry_obj else {}
                
                # Get personal targets
                raw_targets = entry_options.get("notify_target", [])
                if isinstance(raw_targets, str):
                    targets = [raw_targets] if raw_targets else []
                else:
                    targets = list(raw_targets)
                for key in ["notify_target_2", "notify_target_3"]:
                    val = entry_options.get(key)
                    if val and val not in targets:
                        targets.append(val)

                # Get management targets
                raw_mgmt = entry_options.get(CONF_NOTIFY_TARGET_MANAGEMENT, [])
                if isinstance(raw_mgmt, str):
                    targets_mgmt = [raw_mgmt] if raw_mgmt else []
                else:
                    targets_mgmt = list(raw_mgmt)
                    
                from .const import DRINK_TYPES
                drink_name = DRINK_TYPES.get(loai, {}).get("name", loai)
                amount_str = str(int(luong_ml) if luong_ml.is_integer() else luong_ml)

                # Send to personal targets
                if targets:
                    msg_personal = entry_options.get(CONF_DRINK_LOG_NOTIFY_PERSONAL, DEFAULT_DRINK_LOG_NOTIFY_PERSONAL)
                    message_p = msg_personal.replace("{person_name}", coordinator.person_name).replace("{amount}", amount_str).replace("{drink_name}", drink_name)
                    for notify_target in targets:
                        if notify_target:
                            target_service = notify_target.replace("notify.", "")
                            hass.async_create_task(
                                hass.services.async_call("notify", target_service, {"message": message_p, "title": "Ghi nhận đồ uống 💧"}, blocking=False)
                            )

                # Send to management targets
                if targets_mgmt:
                    msg_mgmt = entry_options.get(CONF_DRINK_LOG_NOTIFY_MANAGEMENT, DEFAULT_DRINK_LOG_NOTIFY_MANAGEMENT)
                    message_m = msg_mgmt.replace("{person_name}", coordinator.person_name).replace("{amount}", amount_str).replace("{drink_name}", drink_name)
                    for notify_target in targets_mgmt:
                        if notify_target:
                            target_service = notify_target.replace("notify.", "")
                            hass.async_create_task(
                                hass.services.async_call("notify", target_service, {"message": message_m, "title": "Ghi nhận đồ uống 💧"}, blocking=False)
                            )

            elif call.service == SERVICE_REMOVE_LAST:
                await coordinator.async_remove_last()
                
                # Check notification
                entry_obj = hass.config_entries.async_get_entry(entry_id)
                entry_options = entry_obj.options if entry_obj else {}
                
                # Get personal targets
                raw_targets = entry_options.get("notify_target", [])
                if isinstance(raw_targets, str):
                    targets = [raw_targets] if raw_targets else []
                else:
                    targets = list(raw_targets)
                for key in ["notify_target_2", "notify_target_3"]:
                    val = entry_options.get(key)
                    if val and val not in targets:
                        targets.append(val)

                # Get management targets
                raw_mgmt = entry_options.get(CONF_NOTIFY_TARGET_MANAGEMENT, [])
                if isinstance(raw_mgmt, str):
                    targets_mgmt = [raw_mgmt] if raw_mgmt else []
                else:
                    targets_mgmt = list(raw_mgmt)
                    
                # Send to personal targets
                if targets:
                    msg_personal_remove = "Bạn vừa hoàn tác (xoá) đồ uống gần nhất."
                    for notify_target in targets:
                        if notify_target:
                            target_service = notify_target.replace("notify.", "")
                            hass.async_create_task(
                                    hass.services.async_call("notify", target_service, {"message": msg_personal_remove, "title": "Hoàn tác đồ uống ↩️"}, blocking=False)
                            )

                # Send to management targets
                if targets_mgmt:
                    msg_mgmt_remove = entry_options.get(CONF_DRINK_LOG_NOTIFY_REMOVE, DEFAULT_DRINK_LOG_NOTIFY_REMOVE)
                    message_m = msg_mgmt_remove.replace("{person_name}", coordinator.person_name)
                    for notify_target in targets_mgmt:
                        if notify_target:
                            target_service = notify_target.replace("notify.", "")
                            hass.async_create_task(
                                hass.services.async_call("notify", target_service, {"message": message_m, "title": "Hoàn tác đồ uống ↩️"}, blocking=False)
                            )

            elif call.service == SERVICE_REMOVE_BY_ID:
                await coordinator.async_remove_by_id(call.data[ATTR_EVENT_ID])

            elif call.service == SERVICE_CLEAR_TODAY:
                await coordinator.async_clear_today()

            elif call.service == "log_medicine":
                name = call.data["name"]
                med_type = call.data.get("med_type", "general")
                timestamp_str = call.data.get(ATTR_TIMESTAMP)
                reminder_str = call.data.get("reminder_time")
                
                ts = None
                if timestamp_str:
                    ts = dt_util.parse_datetime(timestamp_str)
                    if ts and ts.tzinfo is None: ts = dt_util.as_utc(ts)
                    
                rm = None
                if reminder_str:
                    rm = dt_util.parse_datetime(reminder_str)
                    if rm and rm.tzinfo is None: rm = dt_util.as_utc(rm)

                await coordinator.async_log_medicine(
                    name=name, med_type=med_type, reminder_time=rm, timestamp=ts
                )

    hass.services.async_register(
        DOMAIN,
        "log_drink",
        handle_service,
        schema=cv.make_entity_service_schema(
            {
                vol.Required("loai"): cv.string,
                vol.Required("luong_ml"): vol.All(
                    vol.Coerce(float), vol.Range(min=1, max=2000)
                ),
                vol.Optional(ATTR_TIMESTAMP): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_LAST,
        handle_service,
        schema=cv.make_entity_service_schema({}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_BY_ID,
        handle_service,
        schema=cv.make_entity_service_schema({vol.Required(ATTR_EVENT_ID): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_TODAY,
        handle_service,
        schema=cv.make_entity_service_schema({}),
    )
    hass.services.async_register(
        DOMAIN,
        "log_medicine",
        handle_service,
        schema=cv.make_entity_service_schema(
            {
                vol.Required("name"): cv.string,
                vol.Optional("med_type"): vol.In(["iron", "antibiotic", "vitamin", "general"]),
                vol.Optional("reminder_time"): cv.string,
                vol.Optional(ATTR_TIMESTAMP): cv.string,
            }
        ),
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a M.A.I Tracker profile from a config entry."""
    options = entry.options
    data = entry.data

    def _get_float(key: str, default: float) -> float:
        return float(options.get(key, data.get(key, default)))

    def _get_bool(key: str, default: bool) -> bool:
        return bool(options.get(key, data.get(key, default)))

    coordinator = CaffeineCoordinator(
        hass=hass,
        entry_id=entry.entry_id,
        person_name=data[CONF_PERSON_NAME],
        half_life_hours=_get_float(CONF_HALF_LIFE_HOURS, DEFAULT_HALF_LIFE_HOURS),
        sleep_safe_mg=_get_float(CONF_SLEEP_SAFE_MG, DEFAULT_SLEEP_SAFE_MG),
        enable_absorption=_get_bool(CONF_ENABLE_ABSORPTION, DEFAULT_ENABLE_ABSORPTION),
        absorption_time_min=_get_float(
            CONF_ABSORPTION_TIME_MIN, DEFAULT_ABSORPTION_TIME_MIN
        ),
    )

    await coordinator.async_load()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload entry when options change so coordinator picks up new settings.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Auto reset lúc nửa đêm
    async def midnight_reset(now: datetime) -> None:
        await coordinator.async_clear_today()
        _LOGGER.info("mai_tracker: midnight auto-reset for %s", coordinator.person_name)

    from homeassistant.helpers.event import async_track_time_change
    entry.async_on_unload(
        async_track_time_change(hass, midnight_reset, hour=0, minute=0, second=0)
    )

    # Listen to mobile app actionable notifications
    async def handle_mobile_action(event):
        action = event.data.get("action", "")
        med_prefix = f"MAIT_MED_LOG_{entry.entry_id}_"
        water_prefix = f"MAIT_WATER_LOG_{entry.entry_id}_"
        
        if action.startswith(med_prefix):
            med_name = action[len(med_prefix):]
            await coordinator.async_log_medicine(name=med_name, med_type="general")
            _LOGGER.info("Medicine %s logged from notification for %s", med_name, coordinator.person_name)
        elif action.startswith(water_prefix):
            amount_str = action[len(water_prefix):]
            try:
                amount = float(amount_str)
                await coordinator.async_log_drink(loai="nuoc_loc", luong_ml=amount)
                _LOGGER.info("Water %s ml logged from notification for %s", amount, coordinator.person_name)
            except ValueError:
                pass

    entry.async_on_unload(
        hass.bus.async_listen("mobile_app_notification_action", handle_mobile_action)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
