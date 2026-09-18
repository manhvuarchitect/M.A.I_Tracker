from typing import Any
from homeassistant.config_entries import ConfigEntry

from ..coordinator import CaffeineCoordinator
from .base import _CaffeineBase
from ..license import get_instance_id

class LicenseStatusSensor(_CaffeineBase):
    """Sensor reporting the license activation status and features tier."""

    _attr_icon = "mdi:shield-key-outline"

    def __init__(self, coordinator: CaffeineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, suffix="license_status")
        self._attr_unique_id = f"{entry.entry_id}_license_status"

    @property
    def native_value(self) -> str:
        if not self.coordinator.data:
            return "Chưa kích hoạt"
        return self.coordinator.data.license_status

    @property
    def icon(self) -> str:
        if self.coordinator.data and self.coordinator.data.is_pro:
            return "mdi:shield-check"
        return "mdi:shield-lock-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        inst_id = get_instance_id(self.hass)
        is_pro = self.coordinator.data.is_pro if self.coordinator.data else False
        tier = self.coordinator.data.license_tier if self.coordinator.data else "FREE"
        expiry = self.coordinator.license_expiry
        
        return {
            "is_pro": is_pro,
            "tier": tier,
            "instance_id": inst_id,
            "expiry": expiry or "N/A",
            "features_unlocked": [
                "Pharmacokinetics Caffeine Decay",
                "BAC & Widmark Drive Safe Calculation",
                "Multi-Wearable Auto-Detection",
                "Sleep Stages & Sleep Score Tracking",
                "Escalating Medicine Actionable Reminders",
                "Dynamic Water Goal (Heat Index)",
                "Custom TTS Announcements",
                "Long-Term Statistics (LTS)"
            ] if is_pro else ["Basic Fluid Intake"]
        }
