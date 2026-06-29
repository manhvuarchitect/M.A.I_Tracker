"""M.A.I Tracker data coordinator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import logging
import math
from typing import Any
import uuid

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import homeassistant.util.dt as dt_util

from .const import (
    DEFAULT_ABSORPTION_TIME_MIN,
    DEFAULT_HALF_LIFE_HOURS,
    DEFAULT_SLEEP_SAFE_MG,
    DOMAIN,
    MAX_EVENT_AGE_MULTIPLIER,
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=1)


from .models import CaffeineEvent, MedicineEvent, CaffeineData
from .utils.caffeine_calc import compute_current_mg, compute_peak_mg, compute_sleep_safe_at, compute_consumed_today_mg, compute_consumed_today_count
from .utils.alcohol_calc import compute_current_bac, compute_drive_safe_at
from .utils.date_helpers import local_midnight_utc

# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------


class CaffeineCoordinator(DataUpdateCoordinator[CaffeineData]):
    """Manages caffeine state for one person."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        person_name: str,
        half_life_hours: float = DEFAULT_HALF_LIFE_HOURS,
        sleep_safe_mg: float = DEFAULT_SLEEP_SAFE_MG,
        enable_absorption: bool = False,
        absorption_time_min: float = DEFAULT_ABSORPTION_TIME_MIN,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_{person_name}",
            update_interval=SCAN_INTERVAL,
        )
        self.entry_id = entry_id
        self.person_name = person_name
        self.half_life_hours = half_life_hours
        self.sleep_safe_mg = sleep_safe_mg
        self.enable_absorption = enable_absorption
        self.absorption_time_min = absorption_time_min
        self.weight_kg = 65.0 # Updated via options
        self.gender = "male" # Updated via options
        self._store: Store = Store(
            hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}_{entry_id}"
        )
        self._events: list[CaffeineEvent] = []
        self._alcohol_events: list[CaffeineEvent] = []
        self._medicines: list[MedicineEvent] = []
        self._caffeine_history: list[dict[str, Any]] = []
        self.water_total: float = 0.0
        self.drinks_total: dict[str, float] = {}
        self._fired_medicines: set[str] = set()
        
        self.aggregated_heart_rate: float | None = None
        self.aggregated_steps: int = 0
        self._last_step_values: dict[str, float] = {}
        self.last_drink_time: datetime | None = None
        # Medicine actionable reminders: dict mapping unique_key to { "name": med_name, "user_1": notify_1, "user_2": notify_2, "fired_at": datetime, "level": 1, "task": CancelableCallback }
        self.active_med_reminders: dict[str, dict[str, Any]] = {}
        self.last_bio_sync: datetime | None = None

    async def async_load(self) -> None:
        """Load persisted events from storage."""
        stored = await self._store.async_load()
        if stored:
            if "events" in stored:
                self._events = [CaffeineEvent.from_dict(e) for e in stored["events"]]
            if "alcohol_events" in stored:
                self._alcohol_events = [CaffeineEvent.from_dict(e) for e in stored["alcohol_events"]]
            if "medicines" in stored:
                self._medicines = [MedicineEvent.from_dict(e) for e in stored["medicines"]]
            if "caffeine_history" in stored:
                self._caffeine_history = stored["caffeine_history"]
            
            today = datetime.now().strftime("%Y-%m-%d")
            if stored.get("date") == today:
                self.water_total = float(stored.get("water_total", 0.0))
                self.drinks_total = stored.get("drinks_total", {})
            else:
                # If a new day started while HA was off, push yesterday's total to history
                last_date = stored.get("date")
                last_total = float(stored.get("last_consumed_today_mg", 0.0))
                if last_date and last_total > 0:
                    self._caffeine_history.append({"date": last_date, "mg": last_total})
                    if len(self._caffeine_history) > 5:
                        self._caffeine_history.pop(0)
                self.water_total = 0.0
                self.drinks_total = {}
                self.aggregated_steps = 0
                self._last_step_values = {}
                
            # Load stored steps if available
            self.aggregated_steps = int(stored.get("aggregated_steps", self.aggregated_steps))
            self._last_step_values = stored.get("last_step_values", self._last_step_values)
            if stored.get("last_drink_time"):
                self.last_drink_time = datetime.fromisoformat(stored["last_drink_time"])
                if self.last_drink_time.tzinfo is None:
                    self.last_drink_time = self.last_drink_time.replace(tzinfo=UTC)
                
        self._prune_old_events()
        _LOGGER.debug("Loaded %d events for %s", len(self._events), self.person_name)

    async def _async_save(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        now = dt_util.utcnow()
        midnight = local_midnight_utc(now)
        today_mg = compute_consumed_today_mg(self._events, midnight)
        
        await self._store.async_save({
            "events": [e.to_dict() for e in self._events],
            "alcohol_events": [e.to_dict() for e in self._alcohol_events],
            "medicines": [e.to_dict() for e in self._medicines],
            "caffeine_history": self._caffeine_history,
            "water_total": self.water_total,
            "drinks_total": self.drinks_total,
            "date": today,
            "last_consumed_today_mg": today_mg,
            "aggregated_steps": self.aggregated_steps,
            "last_step_values": self._last_step_values,
            "last_drink_time": self.last_drink_time.isoformat() if self.last_drink_time else None
        })

    def _prune_old_events(self) -> None:
        cutoff = dt_util.utcnow() - timedelta(
            hours=MAX_EVENT_AGE_MULTIPLIER * self.half_life_hours
        )
        before = len(self._events)
        self._events = [e for e in self._events if e.timestamp > cutoff]
        pruned = before - len(self._events)
        if pruned:
            _LOGGER.debug("Pruned %d stale events for %s", pruned, self.person_name)

    async def _async_update_data(self) -> CaffeineData:
        self._prune_old_events()
        now = dt_util.utcnow()
        abs_min = self.absorption_time_min if self.enable_absorption else 0.0
        current = compute_current_mg(self._events, self.half_life_hours, now, abs_min)
        midnight = local_midnight_utc(now)
        today_mg = compute_consumed_today_mg(self._events, midnight)
        today_count = compute_consumed_today_count(self._events, midnight)

        today_str = datetime.now().strftime("%Y-%m-%d")
        stored = await self._store.async_load()
        if stored and stored.get("date") != today_str:
            # Auto-clear trigger
            last_date = stored.get("date")
            last_total = float(stored.get("last_consumed_today_mg", 0.0))
            if last_date and last_total > 0:
                self._caffeine_history.append({"date": last_date, "mg": last_total})
                if len(self._caffeine_history) > 5:
                    self._caffeine_history.pop(0)
            self.water_total = 0.0
            self.drinks_total = {}
            self.aggregated_steps = 0
            self._last_step_values = {}
            self.last_drink_time = None
            await self._async_save()

        # Compute BAC
        entry = self.hass.config_entries.async_get_entry(self.entry_id)
        if entry:
            self.weight_kg = float(entry.options.get("weight_kg", entry.data.get("weight_kg", 65.0)))
            self.gender = entry.options.get("gender", entry.data.get("gender", "male"))
            
            # Bio Sensors Aggregation
            hr_sensors = entry.options.get("heart_rate_sensors", [])
            if isinstance(hr_sensors, str): hr_sensors = [hr_sensors] if hr_sensors else []
            step_sensors = entry.options.get("step_sensors", [])
            if isinstance(step_sensors, str): step_sensors = [step_sensors] if step_sensors else []
            weight_sensor = entry.options.get("weight_sensor", "")
            
            # Auto Sync Phone Companion Sensors (wake up phone)
            sync_interval_mins = int(entry.options.get("bio_sync_interval", entry.data.get("bio_sync_interval", 60)))
            local_now_check = dt_util.as_local(now)
            if sync_interval_mins > 0 and 7 <= local_now_check.hour < 22:
                # Check if it's time to sync
                should_sync = False
                if self.last_bio_sync is None:
                    should_sync = True
                else:
                    elapsed_sync = (now - self.last_bio_sync).total_seconds() / 60.0
                    if elapsed_sync >= sync_interval_mins:
                        should_sync = True
                
                if should_sync:
                    self.last_bio_sync = now
                    entities_to_update = []
                    entities_to_update.extend(hr_sensors)
                    entities_to_update.extend(step_sensors)
                    if weight_sensor:
                        entities_to_update.append(weight_sensor)
                        
                    entities_to_update = [e for e in entities_to_update if e]
                    if entities_to_update:
                        _LOGGER.info("M.A.I Tracker: Auto-syncing phone companion sensors: %s", entities_to_update)
                        self.hass.async_create_task(
                            self.hass.services.async_call(
                                "homeassistant",
                                "update_entity",
                                {"entity_id": entities_to_update},
                                blocking=False
                            )
                        )

            # 1. Weight Sensor Auto-update
            if weight_sensor:
                w_state = self.hass.states.get(weight_sensor)
                if w_state and w_state.state not in ("unknown", "unavailable"):
                    try:
                        w_val = float(w_state.state)
                        if 30.0 <= w_val <= 200.0:
                            self.weight_kg = w_val
                    except ValueError:
                        pass

            # 2. Heart Rate Fallback Aggregation
            best_hr = None
            best_time = None
            for sensor_id in hr_sensors:
                state_obj = self.hass.states.get(sensor_id)
                if state_obj and state_obj.state not in ("unknown", "unavailable"):
                    try:
                        hr_val = float(state_obj.state)
                        if 30 <= hr_val <= 220:
                            if not best_time or state_obj.last_updated > best_time:
                                best_time = state_obj.last_updated
                                best_hr = hr_val
                    except ValueError:
                        pass
            self.aggregated_heart_rate = round(best_hr, 1) if best_hr is not None else None

            # 3. Step Delta Summation
            max_delta = 0.0
            for sensor_id in step_sensors:
                state_obj = self.hass.states.get(sensor_id)
                if state_obj and state_obj.state not in ("unknown", "unavailable"):
                    try:
                        current_val = float(state_obj.state)
                        last_val = self._last_step_values.get(sensor_id, current_val)
                        delta = current_val - last_val
                        if delta > 0:
                            if delta > max_delta:
                                max_delta = delta
                        elif delta < -1000:
                            # Sensor reset (e.g. at midnight for a daily step tracker)
                            pass 
                        self._last_step_values[sensor_id] = current_val
                    except ValueError:
                        pass
            
            if max_delta > 0:
                self.aggregated_steps += int(max_delta)
                # Auto-hydrate: add 50ml per 1000 steps
                water_to_add = (int(max_delta) / 1000.0) * 50.0
                self.water_total += water_to_add
                _LOGGER.debug("Added %d steps, compensated %.1f ml water", int(max_delta), water_to_add)

            # Medicine Scheduler Logic
            local_now = dt_util.as_local(now)
            current_time_str = local_now.strftime("%H:%M:%S")
            # If TimeSelector doesn't use seconds, we can match prefix
            current_time_short = local_now.strftime("%H:%M")
            today_date_str = local_now.strftime("%Y-%m-%d")
            
            for i in range(1, 11):
                med_name = entry.options.get(f"medicine_{i}_name", "").strip()
                med_time = entry.options.get(f"medicine_{i}_time", "").strip()
                if not med_name or not med_time: continue
                
                # HA time selector usually returns 'HH:MM:SS' or 'HH:MM'
                if current_time_str == med_time or current_time_short == med_time or med_time.startswith(current_time_short):
                    fire_key = f"{today_date_str}_{med_name}_{med_time}"
                    if fire_key not in self._fired_medicines:
                        self._fired_medicines.add(fire_key)
                        
                        notify_target = entry.options.get(f"medicine_{i}_notify", "")
                        notify_secondary = entry.options.get(f"medicine_{i}_notify_secondary", "")
                        tts_target = entry.options.get(f"medicine_{i}_tts", "")
                        
                        # Send TTS
                        if tts_target:
                            msg = f"Đã đến giờ uống thuốc {med_name}. Bạn hãy kiểm tra điện thoại để xác nhận nhé!"
                            self.hass.async_create_task(
                                self.hass.services.async_call("tts", "cloud_say", {
                                    "entity_id": tts_target,
                                    "message": msg
                                }, blocking=False)
                            )
                            
                        # Send Actionable Notification Lớp 1 tới User 1
                        if notify_target:
                            target_service = notify_target.replace("notify.", "")
                            # Unique key identifies this reminder session
                            reminder_key = f"{self.entry_id}_{med_name}_{today_date_str}_{med_time.replace(':', '_')}"
                            
                            # Store in active reminders
                            self.active_med_reminders[reminder_key] = {
                                "name": med_name,
                                "user_1": notify_target,
                                "user_2": notify_secondary,
                                "fired_at": now,
                                "level": 1,
                                "key": reminder_key,
                                "i": i
                            }
                            
                            action_confirm = f"MAIT_MED_CONFIRM_{reminder_key}"
                            action_snooze = f"MAIT_MED_SNOOZE_{reminder_key}"
                            
                            self.hass.async_create_task(
                                self.hass.services.async_call("notify", target_service, {
                                    "message": f"Đến giờ uống thuốc {med_name} rồi sếp! Vui lòng xác nhận.",
                                    "title": "Nhắc nhở Uống Thuốc 💊",
                                    "data": {
                                        "actions": [
                                            {
                                                "action": action_confirm,
                                                "title": "Đã uống"
                                            },
                                            {
                                                "action": action_snooze,
                                                "title": "Nhắc lại sau 15 phút"
                                            }
                                        ]
                                    }
                                }, blocking=False)
                            )

            # Auto reminder Snooze & Escalation Logic (run on every scan interval)
            keys_to_delete = []
            for r_key, reminder in list(self.active_med_reminders.items()):
                fired_at = reminder["fired_at"]
                elapsed_seconds = (now - fired_at).total_seconds()
                
                # Level 1 -> Level 2: if 15 minutes elapsed and user didn't confirm
                if reminder["level"] == 1 and elapsed_seconds >= 900:  # 15 minutes
                    reminder["level"] = 2
                    reminder["fired_at"] = now  # Reset time for Level 2
                    user1_service = reminder["user_1"].replace("notify.", "")
                    
                    action_confirm = f"MAIT_MED_CONFIRM_{r_key}"
                    action_not_taken = f"MAIT_MED_NOTTAKEN_{r_key}"
                    
                    self.hass.async_create_task(
                        self.hass.services.async_call("notify", user1_service, {
                            "message": f"Bạn vẫn chưa xác nhận uống thuốc {reminder['name']}. Vui lòng xác nhận tình trạng.",
                            "title": "Cảnh báo Nhắc Thuốc (Lần 2) 💊",
                            "data": {
                                "actions": [
                                    {
                                        "action": action_confirm,
                                        "title": "Đã uống"
                                    },
                                    {
                                        "action": action_not_taken,
                                        "title": "Chưa uống"
                                    }
                                ]
                            }
                        }, blocking=False)
                    )
                
                # Level 2 Escalation: if 15 minutes elapsed since Level 2 (total 30 mins) with no response
                elif reminder["level"] == 2 and elapsed_seconds >= 900:  # another 15 minutes
                    keys_to_delete.append(r_key)
                    # Escalate to User 2 if configured
                    if reminder["user_2"]:
                        user2_service = reminder["user_2"].replace("notify.", "")
                        self.hass.async_create_task(
                            self.hass.services.async_call("notify", user2_service, {
                                "message": f"Cảnh báo: {self.person_name} đã quá giờ uống thuốc {reminder['name']} 30 phút nhưng hoàn toàn không phản hồi. Vui lòng liên hệ nhắc nhở!",
                                "title": "Giám sát Nhắc Thuốc 🚨"
                            }, blocking=False)
                        )
            
            for r_key in keys_to_delete:
                if r_key in self.active_med_reminders:
                    del self.active_med_reminders[r_key]

            # Water Reminder Logic
            # Only remind between 07:00 and 21:00 local time
            if 7 <= local_now.hour < 21:
                reminder_interval = float(entry.options.get("water_reminder_interval", entry.data.get("water_reminder_interval", 120.0)))
                if reminder_interval > 0:
                    last_time = self.last_drink_time or midnight # fallback to midnight if no drink yet today
                    elapsed_minutes = (now - last_time).total_seconds() / 60.0
                    
                    # We check if we crossed a multiple of reminder_interval in the last minute (to avoid spamming every scan)
                    # For example, if elapsed_minutes is between reminder_interval and reminder_interval + 1.2 minutes
                    if reminder_interval <= elapsed_minutes < reminder_interval + 1.2:
                        hours_elapsed = round(elapsed_minutes / 60.0, 1)
                        if hours_elapsed.is_integer():
                            hours_str = str(int(hours_elapsed))
                        else:
                            hours_str = str(hours_elapsed)
                            
                        # Get targets
                        raw_targets = entry.options.get("notify_target", [])
                        if isinstance(raw_targets, str):
                            notify_targets = [raw_targets] if raw_targets else []
                        else:
                            notify_targets = list(raw_targets)

                        notify_target_2 = entry.options.get("notify_target_2", "")
                        notify_target_3 = entry.options.get("notify_target_3", "")
                        if notify_target_2 and notify_target_2 not in notify_targets:
                            notify_targets.append(notify_target_2)
                        if notify_target_3 and notify_target_3 not in notify_targets:
                            notify_targets.append(notify_target_3)

                        raw_mgmt = entry.options.get("notify_target_management", [])
                        if isinstance(raw_mgmt, str):
                            notify_targets_mgmt = [raw_mgmt] if raw_mgmt else []
                        else:
                            notify_targets_mgmt = list(raw_mgmt)

                        tts_target = entry.options.get("tts_target", "")
                        
                        # Send TTS
                        if tts_target:
                            tts_msg_tpl = entry.options.get("water_reminder_tts", "Sếp ơi, đã {hours} tiếng trôi qua sếp chưa uống thêm nước. Sếp hãy uống một cốc nước lọc nhé!")
                            self.hass.async_create_task(
                                self.hass.services.async_call("tts", "cloud_say", {
                                    "entity_id": tts_target,
                                    "message": tts_msg_tpl.replace("{hours}", hours_str)
                                }, blocking=False)
                            )
                            
                        # Send Notify to Personal Targets (with Actionable Buttons)
                        notify_msg_tpl = entry.options.get("water_reminder_notify", "Đã {hours} tiếng bạn chưa uống thêm nước. Uống nước đi nhé!")
                        message = notify_msg_tpl.replace("{hours}", hours_str)
                        for nt in notify_targets:
                            if nt:
                                target_service = nt.replace("notify.", "")
                                action_250 = f"MAIT_WATER_LOG_{self.entry_id}_250"
                                action_350 = f"MAIT_WATER_LOG_{self.entry_id}_350"
                                self.hass.async_create_task(
                                    self.hass.services.async_call("notify", target_service, {
                                        "message": message,
                                        "title": "Nhắc nhở uống nước 💧",
                                        "data": {
                                            "actions": [
                                                {
                                                    "action": action_250,
                                                    "title": "Đã uống 250ml"
                                                },
                                                {
                                                    "action": action_350,
                                                    "title": "Đã uống 350ml"
                                                }
                                            ]
                                        }
                                    }, blocking=False)
                                )

                        # Send Notify to Management Targets
                        notify_msg_tpl_mgmt = entry.options.get("water_reminder_notify_management", "Đã {hours} tiếng {person_name} chưa uống thêm nước.")
                        message_mgmt = notify_msg_tpl_mgmt.replace("{hours}", hours_str).replace("{person_name}", self.person_name)
                        for nt in notify_targets_mgmt:
                            if nt:
                                target_service = nt.replace("notify.", "")
                                self.hass.async_create_task(
                                    self.hass.services.async_call("notify", target_service, {
                                        "message": message_mgmt,
                                        "title": "Nhắc nhở uống nước 💧"
                                    }, blocking=False)
                                )

        bac = compute_current_bac(self._alcohol_events, self.weight_kg, self.gender, now)
        drive_safe = compute_drive_safe_at(bac, now)

        if self.enable_absorption:
            peak = compute_peak_mg(
                self._events, self.half_life_hours, self.absorption_time_min, now
            )
            # Use peak for sleep safety — level may still be rising
            safe_at = compute_sleep_safe_at(
                peak, self.half_life_hours, self.sleep_safe_mg, now
            )
        else:
            peak = None
            safe_at = compute_sleep_safe_at(
                current, self.half_life_hours, self.sleep_safe_mg, now
            )

        return CaffeineData(
            current_mg=round(current, 1),
            consumed_today_mg=round(today_mg, 1),
            consumed_today_count=today_count,
            sleep_safe_at=safe_at,
            peak_mg=round(peak, 1) if peak is not None else None,
            events=list(self._events),
            water_total=round(self.water_total, 1),
            drinks_total=dict(self.drinks_total),
            alcohol_events=list(self._alcohol_events),
            medicines=list(self._medicines),
            caffeine_history=list(self._caffeine_history),
            current_bac=round(bac, 4),
            drive_safe_at=drive_safe,
            aggregated_heart_rate=self.aggregated_heart_rate,
            aggregated_steps=self.aggregated_steps,
            last_drink_time=self.last_drink_time,
        )

    # ------------------------------------------------------------------
    # Service handlers (called by sensor entity methods)
    # ------------------------------------------------------------------

    async def async_log_drink(
        self,
        loai: str,
        luong_ml: float,
        timestamp: datetime | None = None,
    ) -> str | None:
        """Log a drink, update water and add caffeine event if any."""
        from .const import DRINK_TYPES
        if loai not in DRINK_TYPES:
            _LOGGER.warning("Unknown drink type: %s", loai)
            return None
            
        cfg = DRINK_TYPES[loai]
        
        # Medicine interaction check
        now = timestamp or dt_util.utcnow()
        if cfg["caffeine_per_100ml"] > 0:
            for med in self._medicines:
                if med.med_type in ["iron", "antibiotic"] and (now - med.timestamp).total_seconds() < 7200:
                    _LOGGER.warning("Interaction alert: %s taken within 2 hours of caffeine!", med.name)
                    self.hass.components.persistent_notification.async_create(
                        f"Cảnh báo: Bạn vừa uống {med.name} cách đây chưa tới 2 tiếng. Uống Cafe/Trà bây giờ sẽ làm mất tác dụng của thuốc!",
                        title="M.A.I Tracker Cảnh báo Y tế ⚠️"
                    )

        water_delta = luong_ml * cfg["water_ratio"]
        self.water_total += water_delta
        self.drinks_total[loai] = self.drinks_total.get(loai, 0.0) + luong_ml
        self.last_drink_time = now
        
        caffeine_delta = (luong_ml / 100.0) * cfg["caffeine_per_100ml"]
        
        event_id = None
        if caffeine_delta != 0:
            event = CaffeineEvent(
                id=str(uuid.uuid4()),
                timestamp=now,
                mg=caffeine_delta,
                label=cfg["name"],
            )
            self._events.append(event)
            event_id = event.id
            _LOGGER.info("Logged %.0f mg (%s) for %s", caffeine_delta, cfg["name"], self.person_name)

        alcohol_abv = cfg.get("alcohol_abv", 0.0)
        alcohol_grams = luong_ml * alcohol_abv * 0.789
        if alcohol_grams != 0:
            event = CaffeineEvent(
                id=str(uuid.uuid4()),
                timestamp=now,
                mg=alcohol_grams,
                label=cfg["name"] + " (Alcohol)",
            )
            self._alcohol_events.append(event)

        await self._async_save()
        await self.async_refresh()
        return event_id

    async def async_log_medicine(
        self,
        name: str,
        med_type: str,
        reminder_time: datetime | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Log a medicine event."""
        now = timestamp or dt_util.utcnow()
        event = MedicineEvent(
            id=str(uuid.uuid4()),
            name=name,
            med_type=med_type,
            timestamp=now,
            reminder_time=reminder_time,
        )
        self._medicines.append(event)
        
        # Keep only the last 20 medicines
        if len(self._medicines) > 20:
            self._medicines = self._medicines[-20:]
            
        await self._async_save()
        await self.async_refresh()
        _LOGGER.info("Logged medicine %s for %s", name, self.person_name)

    async def async_set_water_total(self, value: float) -> None:
        """Manually set the total water."""
        self.water_total = value
        await self._async_save()
        await self.async_refresh()
        _LOGGER.info("Manually set water total to %.0f ml for %s", value, self.person_name)

    async def async_remove_last(self) -> bool:
        """Remove the most recent event. Returns True if an event was removed."""
        if not self._events:
            return False
        self._events.sort(key=lambda e: e.timestamp)
        removed = self._events.pop()
        await self._async_save()
        await self.async_refresh()
        _LOGGER.info(
            "Removed last event (%s %.0f mg) for %s",
            removed.label,
            removed.mg,
            self.person_name,
        )
        return True

    async def async_remove_by_id(self, event_id: str) -> bool:
        """Remove an event by ID. Returns True if found and removed."""
        original = len(self._events)
        self._events = [e for e in self._events if e.id != event_id]
        if len(self._events) == original:
            return False
        await self._async_save()
        await self.async_refresh()
        _LOGGER.info("Removed event %s for %s", event_id, self.person_name)
        return True

    async def async_clear_today(self) -> None:
        """Remove all events from today (local time)."""
        now = dt_util.utcnow()
        midnight = local_midnight_utc(now)
        
        # Push to history before clearing
        today_mg = compute_consumed_today_mg(self._events, midnight)
        today_str = dt_util.as_local(now).strftime("%Y-%m-%d")
        if today_mg > 0:
            self._caffeine_history.append({"date": today_str, "mg": today_mg})
            if len(self._caffeine_history) > 5:
                self._caffeine_history.pop(0)
                
        self._events = [e for e in self._events if e.timestamp < midnight]
        self._alcohol_events = [e for e in self._alcohol_events if e.timestamp < midnight]
        self.water_total = 0.0
        self.drinks_total = {}
        self.aggregated_steps = 0
        self._last_step_values = {}
        self.last_drink_time = None
        await self._async_save()
        await self.async_refresh()
        _LOGGER.info("Cleared today's events and water for %s", self.person_name)
