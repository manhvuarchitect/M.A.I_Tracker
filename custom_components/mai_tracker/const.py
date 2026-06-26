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
CONF_MEDICINE_SCHEDULE = "medicine_schedule"
DEFAULT_ENABLE_ABSORPTION = False
DEFAULT_ABSORPTION_TIME_MIN = 15.0
MIN_ABSORPTION_TIME_MIN = 5.0
MAX_ABSORPTION_TIME_MIN = 60.0

CONF_PERSON_NAME = "person_name" # we use this as prefix
CONF_PREFIX = CONF_PERSON_NAME
CONF_HALF_LIFE_HOURS = "half_life_hours"
CONF_SLEEP_SAFE_MG = "sleep_safe_mg"
CONF_LINKED_USER = "linked_user"

# Water & Heat Index
CONF_WATER_GOAL = "water_goal"
CONF_NOTIFY_TARGET = "notify_target"
CONF_TEMP_SENSOR = "temp_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"

# New Feature Constants
CONF_WEIGHT_KG = "weight_kg"
CONF_GENDER = "gender"
CONF_TTS_TARGET = "tts_target"
CONF_TTS_MESSAGE = "tts_message"
CONF_WATER_REMINDER_INTERVAL = "water_reminder_interval"
CONF_WATER_REMINDER_TTS = "water_reminder_tts"
CONF_WATER_REMINDER_NOTIFY = "water_reminder_notify"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_WEIGHT_SENSOR = "weight_sensor"
CONF_DRINK_LOG_NOTIFY = "drink_log_notify"
CONF_DRINK_LOG_NOTIFY_REMOVE = "drink_log_notify_remove"
CONF_NOTIFY_TARGET_MANAGEMENT = "notify_target_management"
CONF_DRINK_LOG_NOTIFY_PERSONAL = "drink_log_notify_personal"
CONF_DRINK_LOG_NOTIFY_MANAGEMENT = "drink_log_notify_management"
CONF_WATER_REMINDER_NOTIFY_MANAGEMENT = "water_reminder_notify_management"

DEFAULT_WEIGHT_KG = 65.0
DEFAULT_GENDER = "male"
DEFAULT_TTS_MESSAGE = "Nhiệt độ hôm nay rất oi bức. Mai Tracker đã tự động tăng mục tiêu nước của bạn thêm {ml} ml. Hãy nhớ uống nhiều nước nhé!"
DEFAULT_WATER_REMINDER_INTERVAL = 120 # Minutes (2 hours)
DEFAULT_WATER_REMINDER_TTS = "Sếp ơi, đã {hours} tiếng trôi qua sếp chưa uống thêm nước. Sếp hãy uống một cốc nước lọc nhé!"
DEFAULT_WATER_REMINDER_NOTIFY = "Đã {hours} tiếng bạn chưa uống thêm nước. Uống nước đi nhé!"
DEFAULT_WATER_REMINDER_NOTIFY_MANAGEMENT = "Đã {hours} tiếng {person_name} chưa uống thêm nước."
DEFAULT_DRINK_LOG_NOTIFY_PERSONAL = "Bạn vừa uống thêm {amount}ml {drink_name}."
DEFAULT_DRINK_LOG_NOTIFY_MANAGEMENT = "{person_name} vừa uống thêm {amount}ml {drink_name}."
DEFAULT_DRINK_LOG_NOTIFY = "{person_name} vừa uống {amount}ml {drink_name}."
DEFAULT_DRINK_LOG_NOTIFY_REMOVE = "{person_name} vừa hoàn tác (xoá) đồ uống gần nhất."

DRINK_TYPES = {
    "nuoc_loc": {"name": "Nước lọc", "water_ratio": 1.0, "caffeine_per_100ml": 0, "alcohol_abv": 0.0},
    "cafe": {"name": "Cà phê", "water_ratio": 0.8, "caffeine_per_100ml": 40, "alcohol_abv": 0.0},
    "tra": {"name": "Trà", "water_ratio": 0.85, "caffeine_per_100ml": 20, "alcohol_abv": 0.0},
    "nuoc_ngot": {"name": "Nước ngọt", "water_ratio": 0.9, "caffeine_per_100ml": 10, "alcohol_abv": 0.0},
    "sua": {"name": "Sữa", "water_ratio": 0.85, "caffeine_per_100ml": 0, "alcohol_abv": 0.0},
    "bia": {"name": "Bia", "water_ratio": 0.95, "caffeine_per_100ml": 0, "alcohol_abv": 0.05},
    "ruou": {"name": "Rượu", "water_ratio": 0.5, "caffeine_per_100ml": 0, "alcohol_abv": 0.40},
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
