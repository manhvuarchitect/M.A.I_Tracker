# M.A.I Tracker (Home Assistant Custom Component)

**Current Version: 2026.09.18.b2**

A powerful Home Assistant integration to track daily fluid intake, manage caffeine half-life, monitor sleep metrics (score, stages, duration, efficiency), track medicines, and calculate heat index.

---

## 🚀 Key Features
- **Feature Lock & License Key Activation (Bản quyền & Khóa tính năng)**: Cơ chế xác thực bản quyền offline an toàn (HMAC-SHA256) giúp kích hoạt các tính năng Pro cao cấp (Dược động học Cafein, BAC, Giấc ngủ, 3 Wearables, Leo thang nhắc thuốc, TTS tùy biến, LTS).
- **Custom TTS Text & Play Button (Phát loa tùy biến linh hoạt)**: Cung cấp entity nhập văn bản `text.mait_{person}_tts_message` và nút bấm `button.mait_{person}_play_tts` để phát trực tiếp câu nói bất kỳ ra loa từ Dashboard hoặc Automation.
- **Long-Term Statistics (LTS)**: Tự động lưu trữ lịch sử lâu dài (ngày, tuần, tháng, năm vĩnh viễn) cho tất cả chỉ số (nước, cafein, bước chân, giấc ngủ, nhịp tim, nhiệt độ) trên Home Assistant.
- **Sleep Index Tracking (Theo dõi chỉ số giấc ngủ)**: Tích hợp đầy đủ 8 chỉ số giấc ngủ chuyên sâu (Điểm số, Thời lượng, Ngủ sâu, REM, Ngủ nông, Thức, Hiệu suất, Trạng thái) tương ứng với từng thiết bị đeo thông minh (Wearable 1..3).
- **Smart Wearables Integration**: Hỗ trợ đồng bộ đa thiết bị đeo (Apple Watch, Garmin, Galaxy Watch...) với cảm biến on-body, pin, calo, nhịp tim, bước chân và giấc ngủ.
- **Profile Cloning (Sao chép cấu hình)**: Easily duplicate complex settings (medicines, environment, notification devices) from an existing user when creating a new one!
- **Medicine Tracking**: Schedule up to 10 medicines with reminder times, actionable mobile notifications, and TTS alerts. Includes interaction warnings (e.g. taking iron/antibiotics near caffeine).
- **Dynamic Water Goal**: Automatically increases your daily water goal on hot/humid days based on the Heat Index.
- **BAC Tracking**: Uses the Widmark formula to track Blood Alcohol Concentration (BAC) and calculate drive-safe time.
- **Advanced Caffeine Tracking**: Uses exponential decay model to track active caffeine in your body.
- **Water Tracking**: Converts drinks (coffee, tea, etc.) into equivalent water intake and tracks against a daily goal.
- **Heat Index Sensor**: Calculates "Feels Like" temperature based on temperature and humidity sensors.
- **Midnight Reset**: Automatically resets your daily water count at midnight while keeping caffeine timeline intact.

---

## 📊 Sensors Created

| Entity | Description |
|--------|-------------|
| `sensor.mait_{person}_water_today` | Total water consumed today (ml) |
| `sensor.mait_{person}_current` | Active caffeine level currently in your body (mg) |
| `sensor.mait_{person}_consumed_today` | Total caffeine consumed today (mg) |
| `sensor.mait_{person}_consumed_today_count` | Number of caffeinated drinks today |
| `sensor.mait_{person}_sleep_safe_at` | The exact time your caffeine will drop below your sleep threshold |
| `sensor.mait_{person}_peak` | Estimated peak caffeine level (if absorption is enabled) |
| `sensor.mait_{person}_heat_index` | Heat Index calculated from Temp & Humidity (°C) |
| `sensor.mait_{person}_sleep_score` | Điểm số chất lượng giấc ngủ (Sleep Score) |
| `sensor.mait_{person}_sleep_duration` | Tổng thời lượng ngủ (Sleep Duration) |
| `sensor.mait_{person}_deep_sleep` | Thời gian ngủ sâu (Deep Sleep) |
| `sensor.mait_{person}_rem_sleep` | Thời gian ngủ REM (REM Sleep) |
| `sensor.mait_{person}_light_sleep` | Thời gian ngủ nông (Light Sleep) |
| `sensor.mait_{person}_awake_time` | Thời gian thức trong đêm (Awake Time) |
| `sensor.mait_{person}_sleep_efficiency` | Hiệu suất giấc ngủ (Sleep Efficiency %) |
| `sensor.mait_{person}_sleep_state` | Trạng thái giấc ngủ thời gian thực (Sleep State) |
| `sensor.mait_{person}_sleep_summary` | Tổng quan tóm tắt giấc ngủ kèm đầy đủ giai đoạn (Summary) |

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
