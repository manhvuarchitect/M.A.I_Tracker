# Mai Drink Tracker

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/HA-2023.1%2B-blue.svg)](https://www.home-assistant.io/)

Track daily fluid intake in Home Assistant. Automatically converts each drink type to water equivalent and tracks caffeine accumulation. Resets at midnight.

---

## Sensors created

| Entity | Description |
|--------|-------------|
| `sensor.{prefix}_water_total` | Total water equivalent today (ml) |
| `sensor.{prefix}_drink_nuoc` | Pure water (ml) |
| `sensor.{prefix}_drink_cafe` | Coffee (ml) |
| `sensor.{prefix}_drink_tra` | Tea (ml) |
| `sensor.{prefix}_drink_sua` | Milk (ml) |
| `sensor.{prefix}_drink_nuoc_ep` | Juice (ml) |
| `sensor.{prefix}_caffeine_total` | Total caffeine today (mg) |

### Sensor attributes

`sensor.{prefix}_water_total` includes:
- `goal_ml` — daily target
- `percent` — % of goal reached
- `remaining_ml` — ml left to reach goal

Each drink sensor includes:
- `water_equivalent_ml` — converted water value
- `caffeine_mg` — caffeine from this drink
- `water_ratio` — conversion ratio used

---

## Services

### `mai_drink_tracker.log`
Log a drink intake.

| Field | Type | Description |
|-------|------|-------------|
| `prefix` | string | (Optional) Target user prefix if multiple users installed (e.g. `ba`, `chi`). |
| `loai` | string | Drink type: `nuoc` / `cafe` / `tra` / `sua` / `nuoc_ep` |
| `luong_ml` | number | Volume in ml. Use negative to undo (e.g. `-100`) |

Example:
```yaml
service: mai_drink_tracker.log
data:
  prefix: ba  # Omit this line if only 1 user is installed
  loai: cafe
  luong_ml: 250
```

### `mai_drink_tracker.reset`
Reset all drink data to zero.

| Field | Type | Description |
|-------|------|-------------|
| `prefix` | string | (Optional) Target user prefix to reset (e.g. `ba`). If omitted, resets all if only 1 user installed. |

---

## Installation via HACS

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add URL: `https://github.com/manhvuarchitect/M.A.I-drink-tracker`
3. Category: Integration
4. Click **Download**
5. Restart Home Assistant
6. Go to Settings → Integrations → Add → **Mai Drink Tracker**
7. Enter your prefix and daily water goal

---

## Water conversion ratios

| Drink | Ratio | Reason |
|-------|-------|--------|
| Water | 1.0 | Direct |
| Coffee | 0.8 | Mild diuretic effect |
| Tea | 0.9 | Mild diuretic effect |
| Milk | 1.0 | High water content |
| Juice | 1.0 | High water content |

---

## Cloning for another household

1. Install via HACS on the new HA instance
2. Add integration with a different prefix (e.g. `ba`, `chi`)
3. All sensors will be prefixed accordingly — no conflicts

---

## File reference

| File | Purpose |
|------|---------|
| `custom_components/mai_drink_tracker/__init__.py` | Core logic, services, midnight reset |
| `custom_components/mai_drink_tracker/sensor.py` | Sensor entities |
| `custom_components/mai_drink_tracker/config_flow.py` | Setup wizard |
| `custom_components/mai_drink_tracker/const.py` | Drink types config — edit here to add new drinks |
| `custom_components/mai_drink_tracker/services.yaml` | Service definitions |
| `custom_components/mai_drink_tracker/translations/` | UI translations (en, vi) |
