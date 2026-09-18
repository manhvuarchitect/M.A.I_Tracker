"""License Key verification and Feature Lock module for M.A.I Tracker."""
from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime
from typing import Any

_LOGGER = logging.getLogger(__name__)

def _get_sec() -> bytes:
    _p1 = bytes([77, 65, 73, 95, 84, 82, 65, 67, 75, 69, 82])
    _p2 = bytes([83, 69, 67, 85, 82, 69, 95, 83, 65, 76, 84])
    _p3 = bytes([50, 48, 50, 54, 95, 77, 73, 68, 65, 82])
    _p4 = bytes([67, 79, 82, 69, 95, 80, 82, 79, 84, 69, 67, 84, 73, 79, 78, 95, 86, 49])
    return b"_".join([_p1, _p2, _p3, _p4])


def get_instance_id(hass: HomeAssistant) -> str:
    """Retrieve the Home Assistant instance unique identifier."""
    # Try getting from core.uuid in hass.data
    uuid_val = hass.data.get("core.uuid")
    if uuid_val:
        return str(uuid_val).replace("-", "")[:8].upper()
    
    # Fallback to local storage or a deterministic hash
    try:
        from homeassistant.helpers.instance_id import async_get
        # If available in modern HA
    except ImportError:
        pass
    
    return "UNIVERSAL"


def generate_signature(tier: str, expiry: str, instance_id: str) -> str:
    """Generate signature for a given license payload."""
    payload = f"{tier.upper()}:{expiry.upper()}:{instance_id.upper()}"
    sig = hmac.new(_get_sec(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return sig[:16].upper()


def verify_license_key(key: str | None, current_instance_id: str = "UNIVERSAL") -> dict[str, Any]:
    """
    Verify a license key offline.
    Key format: MAIT-<TIER>-<EXPIRY>-<INSTANCE_ID>-<SIGNATURE>
    Examples:
      MAIT-PRO-LIFETIME-ALL-A1B2C3D4E5F67890
      MAIT-PRO-20271231-ALL-9F8E7D6C5B4A3210
      MAIT-PRO-LIFETIME-HASS1234-8A7B6C5D4E3F2A1B
    """
    if not key or not isinstance(key, str):
        return {
            "valid": False,
            "tier": "FREE",
            "status": "Chưa kích hoạt (Free Tier)",
            "expiry": None,
            "is_lifetime": False,
            "reason": "missing_key",
        }

    clean_key = key.strip().upper()
    parts = clean_key.split("-")

    if len(parts) != 5 or parts[0] != "MAIT":
        return {
            "valid": False,
            "tier": "FREE",
            "status": "Mã kích hoạt không đúng định dạng",
            "expiry": None,
            "is_lifetime": False,
            "reason": "invalid_format",
        }

    _, tier, expiry, key_instance, signature = parts

    # 1. Verify instance matching (ALL = Universal key, or matches current HA instance)
    if key_instance != "ALL":
        if current_instance_id != "UNIVERSAL" and key_instance != current_instance_id.upper():
            return {
                "valid": False,
                "tier": "FREE",
                "status": f"Mã chỉ dành cho thiết bị {key_instance}",
                "expiry": None,
                "is_lifetime": False,
                "reason": "instance_mismatch",
            }

    # 2. Verify signature
    expected_sig = generate_signature(tier, expiry, key_instance)
    if not hmac.compare_digest(signature, expected_sig):
        return {
            "valid": False,
            "tier": "FREE",
            "status": "Mã kích hoạt không hợp lệ (Sai chữ ký)",
            "expiry": None,
            "is_lifetime": False,
            "reason": "invalid_signature",
        }

    # 3. Verify expiration
    is_lifetime = (expiry == "LIFETIME")
    if not is_lifetime:
        try:
            exp_date = datetime.strptime(expiry, "%Y%m%d").date()
            today = datetime.now().date()
            if today > exp_date:
                return {
                    "valid": False,
                    "tier": "FREE",
                    "status": f"Mã bản quyền đã hết hạn vào ngày {exp_date.strftime('%d/%m/%Y')}",
                    "expiry": exp_date.isoformat(),
                    "is_lifetime": False,
                    "reason": "expired",
                }
            expiry_str = exp_date.strftime("%d/%m/%Y")
        except ValueError:
            return {
                "valid": False,
                "tier": "FREE",
                "status": "Ngày hết hạn không hợp lệ",
                "expiry": None,
                "is_lifetime": False,
                "reason": "invalid_date",
            }
    else:
        expiry_str = "Vĩnh viễn"

    return {
        "valid": True,
        "tier": tier,
        "status": f"Bản quyền {tier} ({expiry_str})",
        "expiry": expiry_str,
        "is_lifetime": is_lifetime,
        "reason": "active",
    }
