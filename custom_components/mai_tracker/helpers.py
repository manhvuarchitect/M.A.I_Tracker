"""Helper functions for M.A.I Tracker."""

from __future__ import annotations

import logging
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_LINKED_USER

_LOGGER = logging.getLogger(__name__)

async def async_get_user_options(hass: HomeAssistant) -> list[dict[str, str]]:
    """Get list of active Home Assistant users for config flows."""
    try:
        users = await hass.auth.async_get_users()
        options = []
        for u in users:
            if u.is_active:
                name = u.name or u.username or "Chưa đặt tên"
                options.append({"value": u.id, "label": name})
        # Sort by label
        options.sort(key=lambda x: x["label"])
        return options
    except Exception as err:
        _LOGGER.error("Error fetching Home Assistant users: %s", err)
        return []

def resolve_entry_id_by_user_id(hass: HomeAssistant, user_id: str | None) -> str | None:
    """Resolve the M.A.I Tracker config entry ID associated with a Home Assistant user ID."""
    if not user_id:
        return None
        
    for entry_id, coordinator in hass.data.get(DOMAIN, {}).items():
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry:
            linked_user = entry.options.get(CONF_LINKED_USER, entry.data.get(CONF_LINKED_USER))
            if linked_user == user_id:
                return entry_id
                
    return None
