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
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


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

    # Load sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # ── Service: log drink ────────────────────────────────────────
    async def handle_log(call: ServiceCall) -> None:
        loai: str = call.data["loai"]
        luong_ml: float = call.data["luong_ml"]

        state = hass.data[DOMAIN][entry.entry_id]
        d = state["data"]

        if loai not in DRINK_TYPES:
            _LOGGER.warning("mai_drink_tracker: unknown drink type '%s'", loai)
            return

        cfg = DRINK_TYPES[loai]

        # Cập nhật ml từng loại (clamp >= 0)
        current = d["drinks"].get(loai, 0.0)
        d["drinks"][loai] = max(current + luong_ml, 0.0)

        # Cập nhật tổng caffeine
        caffeine_delta = (luong_ml / 100.0) * cfg["caffeine_per_100ml"]
        d["caffeine_total"] = max(d.get("caffeine_total", 0.0) + caffeine_delta, 0.0)

        # Cập nhật tổng nước quy đổi
        water_delta = luong_ml * cfg["water_ratio"]
        d["water_total"] = max(d.get("water_total", 0.0) + water_delta, 0.0)

        await state["store"].async_save(d)

        # Cập nhật sensors
        async_dispatcher_send(hass, f"{DOMAIN}_updated_{entry.entry_id}")
        _LOGGER.debug(
            "Logged %sml of %s | water_total=%.0f | caffeine=%.1fmg",
            luong_ml, loai, d["water_total"], d["caffeine_total"],
        )

    # ── Service: reset ────────────────────────────────────────────
    async def handle_reset(call: ServiceCall) -> None:
        state = hass.data[DOMAIN][entry.entry_id]
        state["data"] = _default_data()
        await state["store"].async_save(state["data"])
        async_dispatcher_send(hass, f"{DOMAIN}_updated_{entry.entry_id}")
        _LOGGER.info("mai_drink_tracker: reset for entry %s", entry.entry_id)

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


# Import ở cuối để tránh circular import
from homeassistant.helpers.dispatcher import async_dispatcher_send  # noqa: E402
