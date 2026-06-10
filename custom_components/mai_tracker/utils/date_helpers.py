from datetime import datetime
import homeassistant.util.dt as dt_util

def local_midnight_utc(now_utc: datetime) -> datetime:
    "Return today's local midnight as a UTC datetime."
    local_now = dt_util.as_local(now_utc)
    midnight_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return dt_util.as_utc(midnight_local)

