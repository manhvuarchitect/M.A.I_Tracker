# M.A.I Tracker (Home Assistant Custom Component)

**Current Version: 2.0.0**

A powerful Home Assistant integration to track daily fluid intake, manage caffeine half-life, monitor sleep-safe caffeine levels, and calculate heat index. This is a rebuilt and optimized version based on `caffeine_tracker`.

---

## 🚀 Features in v2.0.0
- **Advanced Caffeine Tracking**: Uses exponential decay model to track active caffeine in your body.
- **Water Tracking**: Converts drinks (coffee, tea, etc.) into equivalent water intake and tracks against a daily goal.
- **Heat Index Sensor**: Calculates "Feels Like" temperature based on temperature and humidity sensors.
- **Smart Notifications**: Automatically notifies your phone when a drink is logged.
- **Midnight Reset**: Automatically resets your daily water count at midnight while keeping caffeine timeline intact.

---

## 📊 Sensors Created

| Entity | Description |
|--------|-------------|
| `sensor.{prefix}_water_today` | Total water consumed today (ml) |
| `sensor.{prefix}_current` | Active caffeine level currently in your body (mg) |
| `sensor.{prefix}_consumed_today` | Total caffeine consumed today (mg) |
| `sensor.{prefix}_consumed_today_count` | Number of caffeinated drinks today |
| `sensor.{prefix}_sleep_safe_at` | The exact time your caffeine will drop below your sleep threshold |
| `sensor.{prefix}_peak` | Estimated peak caffeine level (if absorption is enabled) |
| `sensor.{prefix}_heat_index` | Heat Index calculated from Temp & Humidity (°C) |

---

## 🛠️ Services

### `mai_tracker.log_drink`
Log a drink intake.

| Field | Type | Description |
|-------|------|-------------|
| `loai` | string | Drink type: `nuoc_loc`, `cafe`, `tra`, `nuoc_ngot`, `sua`, `bia` |
| `luong_ml` | number | Volume in ml. |

Example:
```yaml
service: mai_tracker.log_drink
target:
  entity_id: sensor.manh_current
data:
  loai: cafe
  luong_ml: 250
```

---

## 📥 Installation via HACS

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add URL: `https://github.com/manhvuarchitect/M.A.I_Tracker`
3. Category: Integration
4. Click **Download** (Select `main` from version dropdown to get the absolute latest if `2.0.0` is cached).
5. Restart Home Assistant
6. Go to Settings → Devices & Services → Add Integration → **M.A.I Tracker**
7. Enter your profile settings (Name, Water Goal, Notification device, etc.)

---

## 💧 Water Conversion Ratios

| Drink | Water Ratio | Caffeine per 100ml |
|-------|-------|--------|
| Nước lọc (Water) | 1.0 | 0 mg |
| Cà phê (Coffee) | 0.8 | 40 mg |
| Trà (Tea) | 0.85 | 20 mg |
| Nước ngọt (Soda) | 0.9 | 10 mg |
| Sữa (Milk) | 0.85 | 0 mg |
| Bia (Beer) | 0.95 | 0 mg |
