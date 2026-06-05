"""Mai Drink Tracker — Custom Integration for Home Assistant.

Tracks daily fluid intake (water, coffee, tea, etc.),
converts each drink type to water equivalent, and exposes
sensors + services for use in automations and dashboards.

Data is persisted in .storage/mai_drink_tracker so it
survives HA restarts. Auto-resets at midnight.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
    DRINK_TYPES,
    SERVICE_LOG,
    SERVICE_RESET,
    CONF_PREFIX,
    CONF_NOTIFY_TARGET,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "number"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Mai Drink Tracker component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mai Drink Tracker from a config entry."""
    prefix = entry.data.get(CONF_PREFIX, "")
    storage_key = f"{STORAGE_KEY}_{prefix}" if prefix else STORAGE_KEY

    store = Store(hass, STORAGE_VERSION, storage_key)
    data = await store.async_load()

    if data is None:
        data = _default_data()

    # Nếu ngày lưu khác hôm nay → reset
    today = datetime.now().strftime("%Y-%m-%d")
    if data.get("date") != today:
        data = _default_data()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "store": store,
        "data": data,
        "entry": entry,
    }

    # Đăng ký listener để reload khi options thay đổi
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Load sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # ── Services ──────────────────────────────────────────────────
    if not hass.services.has_service(DOMAIN, SERVICE_LOG):
        async def handle_log(call: ServiceCall) -> None:
            prefix_arg = call.data.get("prefix", "").strip().lower()
            loai: str = call.data.get("loai")
            luong_ml: float = call.data.get("luong_ml")

            target_state = None
            for state in hass.data.get(DOMAIN, {}).values():
                if state["entry"].data.get(CONF_PREFIX, "").lower() == prefix_arg:
                    target_state = state
                    break
            
            if not target_state and len(hass.data.get(DOMAIN, {})) == 1:
                target_state = list(hass.data[DOMAIN].values())[0]

            if not target_state:
                _LOGGER.warning("mai_drink_tracker: No config entry found for prefix '%s'", prefix_arg)
                return

            d = target_state["data"]
            if loai not in DRINK_TYPES:
                _LOGGER.warning("mai_drink_tracker: unknown drink type '%s'", loai)
                return

            cfg = DRINK_TYPES[loai]
            current = d["drinks"].get(loai, 0.0)
            d["drinks"][loai] = max(current + luong_ml, 0.0)
            
            caffeine_delta = (luong_ml / 100.0) * cfg["caffeine_per_100ml"]
            d["caffeine_total"] = max(d.get("caffeine_total", 0.0) + caffeine_delta, 0.0)
            
            water_delta = luong_ml * cfg["water_ratio"]
            d["water_total"] = max(d.get("water_total", 0.0) + water_delta, 0.0)

            await target_state["store"].async_save(d)
            async_dispatcher_send(hass, f"{DOMAIN}_updated_{target_state['entry'].entry_id}")
            
            # Xử lý gửi thông báo nếu có cấu hình
            entry_options = target_state["entry"].options
            notify_target = entry_options.get(CONF_NOTIFY_TARGET)
            if notify_target:
                message = f"Tài khoản {target_state['entry'].data.get(CONF_PREFIX)} vừa uống thêm {luong_ml}ml {cfg['name']}."
                target_service = notify_target.replace("notify.", "")
                hass.async_create_task(
                    hass.services.async_call("notify", target_service, {"message": message, "title": "Ghi nhận đồ uống 💧"}, blocking=False)
                )

            _LOGGER.debug(
                "Logged %sml of %s for prefix %s",
                luong_ml, loai, target_state['entry'].data.get(CONF_PREFIX)
            )

        async def handle_reset(call: ServiceCall | None) -> None:
            # Nếu call = None (từ midnight), reset tất cả
            if call is None:
                for state in hass.data.get(DOMAIN, {}).values():
                    state["data"] = _default_data()
                    await state["store"].async_save(state["data"])
                    async_dispatcher_send(hass, f"{DOMAIN}_updated_{state['entry'].entry_id}")
                return

            prefix = call.data.get("prefix", "").strip().lower()
            target_state = None
            for state in hass.data.get(DOMAIN, {}).values():
                if state["entry"].data.get(CONF_PREFIX, "").lower() == prefix:
                    target_state = state
                    break
            
            if not target_state and len(hass.data.get(DOMAIN, {})) == 1:
                target_state = list(hass.data[DOMAIN].values())[0]

            if not target_state:
                _LOGGER.warning("mai_drink_tracker: No config entry found for prefix '%s' to reset", prefix)
                return

            target_state["data"] = _default_data()
            await target_state["store"].async_save(target_state["data"])
            async_dispatcher_send(hass, f"{DOMAIN}_updated_{target_state['entry'].entry_id}")

        hass.services.async_register(DOMAIN, SERVICE_LOG, handle_log)
        hass.services.async_register(DOMAIN, SERVICE_RESET, handle_reset)

    # ── Auto reset lúc nửa đêm ───────────────────────────────────
    async def midnight_reset(now: datetime) -> None:
        await handle_reset(None)
        _LOGGER.info("mai_drink_tracker: midnight auto-reset")

    async_track_time_change(hass, midnight_reset, hour=0, minute=0, second=0)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        # Xóa services nếu không còn entry nào
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_LOG)
            hass.services.async_remove(DOMAIN, SERVICE_RESET)
    return unload_ok


def _default_data() -> dict[str, Any]:
    """Trả về data mặc định cho 1 ngày mới."""
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "drinks": {k: 0.0 for k in DRINK_TYPES},
        "water_total": 0.0,
        "caffeine_total": 0.0,
    }


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)

# Import ở cuối để tránh circular import
from homeassistant.helpers.dispatcher import async_dispatcher_send  # noqa: E402
