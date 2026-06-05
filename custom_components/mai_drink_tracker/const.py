"""Constants for Mai Drink Tracker.

Thêm loại đồ uống mới: copy 1 entry trong DRINK_TYPES,
điền caffeine_per_100ml và water_ratio. Không cần sửa file khác.

Entity ID pattern: {prefix}_mvadt_{key}
  mvadt = ManhVuArchitect Drink Tracker
  Ví dụ prefix "mai": number.mai_mvadt_cafe, sensor.mai_mvadt_caffeine
"""

DOMAIN = "mai_drink_tracker"
STORAGE_KEY = "mai_drink_tracker"
STORAGE_VERSION = 1

CONF_PREFIX = "prefix"
CONF_WATER_GOAL = "water_goal"
CONF_NOTIFY_TARGET = "notify_target"
CONF_TEMP_SENSOR = "temp_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"

# Cấu hình Caffeine
CONF_ABSORPTION_TIME_MIN = "absorption_time_min"
CONF_ENABLE_ABSORPTION = "enable_absorption"
CONF_HALF_LIFE_HOURS = "half_life_hours"
CONF_SLEEP_SAFE_MG = "sleep_safe_mg"
DEFAULT_ABSORPTION_TIME_MIN = 45.0
DEFAULT_ENABLE_ABSORPTION = False
DEFAULT_HALF_LIFE_HOURS = 5.0
DEFAULT_SLEEP_SAFE_MG = 50.0
MAX_ABSORPTION_TIME_MIN = 120.0
MAX_HALF_LIFE_HOURS = 24.0
MIN_ABSORPTION_TIME_MIN = 5.0
MIN_HALF_LIFE_HOURS = 1.0
MAX_EVENT_AGE_MULTIPLIER = 5.0

SERVICE_LOG = "log"
SERVICE_RESET = "reset"

# Namespace cố định — không đổi, đảm bảo entity ID duy nhất
MVADT = "mvadt"

# ─────────────────────────────────────────────────────────────────
# DRINK TYPES CONFIG
# caffeine_per_100ml : mg caffeine mỗi 100ml (0 nếu không có)
# water_ratio        : tỉ lệ quy đổi sang nước uống hiệu quả
#                      1.0 = 100ml → 100ml nước
#                      0.8 = 100ml cafe → 80ml nước (lợi tiểu nhẹ)
# icon               : MDI icon
# ─────────────────────────────────────────────────────────────────
DRINK_TYPES: dict = {
    "nuoc": {
        "name": "Nước lọc",
        "icon": "mdi:water",
        "caffeine_per_100ml": 0,
        "water_ratio": 1.0,
    },
    "cafe": {
        "name": "Cafe",
        "icon": "mdi:coffee",
        "caffeine_per_100ml": 40,
        "water_ratio": 0.8,
    },
    "tra": {
        "name": "Trà",
        "icon": "mdi:tea",
        "caffeine_per_100ml": 20,
        "water_ratio": 0.9,
    },
    "sua": {
        "name": "Sữa",
        "icon": "mdi:cup",
        "caffeine_per_100ml": 0,
        "water_ratio": 1.0,
    },
    "nuoc_ep": {
        "name": "Nước ép",
        "icon": "mdi:fruit-watermelon",
        "caffeine_per_100ml": 0,
        "water_ratio": 1.0,
    },
}

# Entity key constants — {prefix}_mvadt_{KEY}
# Ví dụ prefix="mai": number.mai_mvadt_water_total
KEY_WATER_TOTAL    = "water_total"
KEY_CAFFEINE_TOTAL = "caffeine_total"
