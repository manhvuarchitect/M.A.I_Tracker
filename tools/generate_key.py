"""M.A.I Tracker - License Key Generator Tool.

Usage:
  py tools/generate_key.py
  py tools/generate_key.py --tier PRO --expiry LIFETIME --instance ALL
  py tools/generate_key.py --tier PRO --expiry 20271231 --instance ALL
  py tools/generate_key.py --tier PRO --expiry 20261231 --instance 8A1B2C3D
"""
import argparse
import hashlib
import hmac
import sys

_LICENSE_SECRET = b"MAI_TRACKER_SECURE_SALT_2026_MIDAR_CORE_PROTECTION_V1"

def generate_key(tier: str = "PRO", expiry: str = "LIFETIME", instance_id: str = "ALL") -> str:
    tier = tier.upper().strip()
    expiry = expiry.upper().strip()
    instance_id = instance_id.upper().strip()
    
    payload = f"{tier}:{expiry}:{instance_id}"
    sig = hmac.new(_LICENSE_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()[:16].upper()
    
    key = f"MAIT-{tier}-{expiry}-{instance_id}-{sig}"
    return key

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="M.A.I Tracker License Key Generator")
    parser.add_argument("--tier", default="PRO", help="License Tier (default: PRO)")
    parser.add_argument("--expiry", default="LIFETIME", help="Expiry in YYYYMMDD format or LIFETIME (default: LIFETIME)")
    parser.add_argument("--instance", default="ALL", help="Home Assistant Instance ID or ALL for universal key (default: ALL)")
    
    args = parser.parse_args()
    key = generate_key(args.tier, args.expiry, args.instance)
    
    print("\n" + "=" * 60)
    print("        M.A.I TRACKER - LICENSE KEY GENERATOR")
    print("=" * 60)
    print(f"  Gói bản quyền (Tier)       : {args.tier.upper()}")
    print(f"  Hạn sử dụng (Expiry)       : {args.expiry.upper()}")
    print(f"  Mã thiết bị (Instance ID)  : {args.instance.upper()}")
    print("-" * 60)
    print(f"  🔑 LICENSE KEY             : {key}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
