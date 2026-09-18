"""Sensor platform for M.A.I Tracker."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import CaffeineCoordinator
from .sensors.caffeine import (
    CaffeineCurrentSensor,
    CaffeineConsumedTodaySensor,
    CaffeineConsumedTodayCountSensor,
    WaterConsumedTodaySensor,
    CaffeineSleepSafeAtSensor,
    CaffeinePercentSensor,
    CaffeinePeakSensor,
    CaffeineCrashRiskSensor,
    CaffeineHistorySensor,
)
from .sensors.alcohol import BACLevelSensor, DriveSafeAtSensor
from .sensors.bio import LastMedicineSensor, AggregatedHeartRateSensor, AggregatedStepsSensor, WeightSensor
from .sensors.sleep import (
    SleepScoreSensor,
    SleepDurationSensor,
    DeepSleepSensor,
    RemSleepSensor,
    LightSleepSensor,
    SleepAwakeSensor,
    SleepEfficiencySensor,
    SleepStateSensor,
    SleepSummarySensor,
)
from .sensors.environment import HeatIndexSensor, DynamicWaterGoalSensor
from .sensors.license import LicenseStatusSensor
from .sensors.base import _CaffeineBase

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: CaffeineCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[_CaffeineBase] = [
        LicenseStatusSensor(coordinator, entry),
        WaterConsumedTodaySensor(coordinator, entry),
        CaffeineCurrentSensor(coordinator, entry),
        CaffeineConsumedTodaySensor(coordinator, entry),
        CaffeineConsumedTodayCountSensor(coordinator, entry),
        CaffeineSleepSafeAtSensor(coordinator, entry),
        CaffeinePercentSensor(coordinator, entry),
        BACLevelSensor(coordinator, entry),
        DriveSafeAtSensor(coordinator, entry),
        LastMedicineSensor(coordinator, entry),
        CaffeineCrashRiskSensor(coordinator, entry),
        CaffeineHistorySensor(coordinator, entry),
        WeightSensor(coordinator, entry),
    ]
    if coordinator.enable_absorption:
        entities.append(CaffeinePeakSensor(coordinator, entry))
        
    hr_sensors = entry.options.get("heart_rate_sensors", entry.data.get("heart_rate_sensors", []))
    if hr_sensors:
        entities.append(AggregatedHeartRateSensor(coordinator, entry))
        
    step_sensors = entry.options.get("step_sensors", entry.data.get("step_sensors", []))
    if step_sensors:
        entities.append(AggregatedStepsSensor(coordinator, entry))

    temp_sensor = entry.options.get("temp_sensor", entry.data.get("temp_sensor", ""))
    humidity_sensor = entry.options.get("humidity_sensor", entry.data.get("humidity_sensor", ""))
    weather_entity = entry.options.get("weather_entity", entry.data.get("weather_entity", ""))
    
    if (temp_sensor and humidity_sensor) or weather_entity:
        entities.append(HeatIndexSensor(coordinator.hass, entry, temp_sensor, humidity_sensor, weather_entity, coordinator.person_name))
        entities.append(DynamicWaterGoalSensor(coordinator.hass, entry, coordinator))

    has_sleep_config = False
    for i in range(1, 4):
        for key in ("sleep_score", "sleep_duration", "sleep_deep", "sleep_rem", "sleep_light", "sleep_awake", "sleep_efficiency", "sleep_state"):
            if entry.options.get(f"wearable_{i}_{key}", entry.data.get(f"wearable_{i}_{key}", "")):
                has_sleep_config = True
                break
        if has_sleep_config:
            break

    if has_sleep_config:
        entities.extend([
            SleepScoreSensor(coordinator, entry),
            SleepDurationSensor(coordinator, entry),
            DeepSleepSensor(coordinator, entry),
            RemSleepSensor(coordinator, entry),
            LightSleepSensor(coordinator, entry),
            SleepAwakeSensor(coordinator, entry),
            SleepEfficiencySensor(coordinator, entry),
            SleepStateSensor(coordinator, entry),
            SleepSummarySensor(coordinator, entry),
        ])

    async_add_entities(entities)
