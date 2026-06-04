"""Constants for Mai Drink Tracker.

Thêm loại đồ uống mới: copy 1 entry trong DRINK_TYPES,
điền caffeine_per_100ml và water_ratio. Không cần sửa file khác.
"""

DOMAIN = "mai_drink_tracker"
STORAGE_KEY = "mai_drink_tracker"
STORAGE_VERSION = 1

CONF_PREFIX = "prefix"
CONF_WATER_GOAL = "water_goal"

SERVICE_LOG = "log"
SERVICE_RESET = "reset"

# ─────────────────────────────────────────────────────────────────
# DRINK TYPES CONFIG
# caffeine_per_100ml : mg caffeine mỗi 100ml (0 nếu không có)
# water_ratio        : tỉ lệ quy đổi sang nước uống hiệu quả
#                      1.0 = 100ml → 100ml nước
#                      0.8 = 100ml cafe → 80ml nước (lợi tiểu nhẹ)
# icon               : MDI icon cho sensor
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

# Sensor IDs (tự động prefix bằng entry prefix khi setup)
SENSOR_WATER_TOTAL    = "water_total"
SENSOR_WATER_PURE     = "nuoc"
SENSOR_CAFE           = "cafe"
SENSOR_TRA            = "tra"
SENSOR_SUA            = "sua"
SENSOR_NUOC_EP        = "nuoc_ep"
SENSOR_CAFFEINE_TOTAL = "caffeine_total"
