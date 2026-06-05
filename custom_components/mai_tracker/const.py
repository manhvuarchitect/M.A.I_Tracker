"""Constants for the M.A.I Tracker integration."""

from __future__ import annotations

DOMAIN = "mai_tracker"
STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = "mai_tracker"

DEFAULT_HALF_LIFE_HOURS = 5.0
DEFAULT_SLEEP_SAFE_MG = 50.0
MIN_HALF_LIFE_HOURS = 3.0
MAX_HALF_LIFE_HOURS = 10.0
# Events older than this multiple of half-life contribute < 1% — safe to prune
MAX_EVENT_AGE_MULTIPLIER = 7

CONF_ENABLE_ABSORPTION = "enable_absorption"
CONF_ABSORPTION_TIME_MIN = "absorption_time_min"
DEFAULT_ENABLE_ABSORPTION = False
DEFAULT_ABSORPTION_TIME_MIN = 15.0
MIN_ABSORPTION_TIME_MIN = 5.0
MAX_ABSORPTION_TIME_MIN = 60.0

CONF_PERSON_NAME = "person_name" # we use this as prefix
CONF_PREFIX = CONF_PERSON_NAME
CONF_HALF_LIFE_HOURS = "half_life_hours"
CONF_SLEEP_SAFE_MG = "sleep_safe_mg"

# Water & Heat Index
CONF_WATER_GOAL = "water_goal"
CONF_NOTIFY_TARGET = "notify_target"
CONF_TEMP_SENSOR = "temp_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"

DRINK_TYPES = {
    "nuoc_loc": {"name": "Nước lọc", "water_ratio": 1.0, "caffeine_per_100ml": 0},
    "cafe": {"name": "Cà phê", "water_ratio": 0.8, "caffeine_per_100ml": 40},
    "tra": {"name": "Trà", "water_ratio": 0.85, "caffeine_per_100ml": 20},
    "nuoc_ngot": {"name": "Nước ngọt", "water_ratio": 0.9, "caffeine_per_100ml": 10},
    "sua": {"name": "Sữa", "water_ratio": 0.85, "caffeine_per_100ml": 0},
    "bia": {"name": "Bia", "water_ratio": 0.95, "caffeine_per_100ml": 0},
}

ATTR_EVENTS = "events"
ATTR_EVENT_ID = "event_id"
ATTR_MG = "mg"
ATTR_LABEL = "label"
ATTR_TIMESTAMP = "timestamp"

SERVICE_LOG_CONSUMPTION = "log_consumption"
SERVICE_REMOVE_LAST = "remove_last_consumption"
SERVICE_REMOVE_BY_ID = "remove_consumption"
SERVICE_CLEAR_TODAY = "clear_today"
