# Changelog - M.A.I Tracker

Tất cả các thay đổi, tính năng mới và bản sửa lỗi của integration **M.A.I Tracker** được ghi nhận chi tiết tại đây theo định dạng phiên bản `YYYY.MM.DD.bx`.

---

## [2026.09.18.b2] - 2026-09-18

### ✨ Tính năng mới: Khóa Tính Năng & Kích Hoạt Bản Quyền (License Key)
- **Cơ chế Khóa Tính Năng (Feature Lock & Free/Pro Tiers)**:
  - Bản Miễn Phí (Free Tier): Theo dõi lượng nước uống cơ bản.
  - Bản Kích Hoạt (Pro Tier): Mở khóa toàn bộ các tính năng cao cấp (Dược động học Cafein, Nồng độ cồn BAC, 8 chỉ số giấc ngủ, 3 Thiết bị đeo, Nhắc thuốc leo thang, Phát loa TTS tùy biến, Thống kê LTS).
- **Xác thực Bản quyền Offline (HMAC-SHA256)**:
  - Tích hợp module xác thực chữ ký điện tử an toàn `license.py` hoạt động độc lập ngay trên Home Assistant không cần internet.
  - Hỗ trợ khóa key theo mã thiết bị (Instance ID) hoặc key vạn năng (Universal Key) với hạn sử dụng (Tháng/Năm/Vĩnh viễn).
- **Bộ công cụ tạo mã bản quyền cho Quản trị viên (`tools/generate_key.py`)**:
  - Hỗ trợ tạo License Key linh hoạt theo từng khách hàng.
- **Thực thể Trạng thái Bản quyền (`sensor.mait_{person}_license_status`)**:
  - Báo cáo rõ ràng trạng thái kích hoạt, thời hạn và danh sách các tính năng được mở khóa.

---

## [2026.09.18.b1] - 2026-09-18

### 🐛 Sửa lỗi & Tối ưu hóa TTS (Bug Fixes & Improvements)
- **Tương thích toàn diện với tất cả TTS Engines**: Nâng cấp hàm phát âm thanh thông minh `_async_call_tts`, tự động nhận diện và gọi đúng dịch vụ TTS đang có trên Home Assistant (`google_translate_say`, `cloud_say`, `piper_say`, hoặc `tts.speak`), giúp loa Google Home Mini, Nest Hub, Echo... phát âm thanh tức thì mà không phụ thuộc vào Nabu Casa Cloud.

---

## [2026.09.03.b1] - 2026-09-03

### ✨ Tính năng mới (Features)
- **Bổ sung Entity nhập nội dung & nút phát loa TTS tùy biến**:
  - Tạo entity nhập văn bản `text.mait_{person}_tts_message`: Cho phép nhập trực tiếp nội dung câu thông báo tùy ý từ Dashboard.
  - Tạo entity nút bấm `button.mait_{person}_play_tts`: Nhấn nút để phát ngay nội dung vừa nhập ra Loa phát thanh (TTS Speaker / Media Player) đã chọn ở Bước 4/5.
  - Bổ sung service `mai_tracker.speak`: Hỗ trợ phát nhanh câu nói tùy biến từ Script / Automation.

---

## [2026.08.31.b1] - 2026-08-31

### ✨ Tính năng mới (Features)
- **Tích hợp Long-Term Statistics (LTS) toàn diện**:
  - Hỗ trợ lưu trữ và vẽ biểu đồ lịch sử lâu dài (theo tuần, tháng, năm vĩnh viễn) trực tiếp trên Home Assistant Dashboard (Statistics Graph Card, ApexCharts, Plotly).
  - Bổ sung cảm biến tổng lượng nước tiêu thụ `sensor.mait_{person}_water_today` với `state_class = TOTAL_INCREASING`, `device_class = WATER` và `unit_of_measurement = ml`.
  - Khai báo chuẩn hóa `state_class`, `device_class`, đơn vị đo lường (`unit_of_measurement`) và độ chính xác hiển thị (`suggested_display_precision`) cho toàn bộ cảm biến:
    - **Nước & Đồ uống**: `water_today` (`ml`, `TOTAL_INCREASING`), `consumed_today_count` (`cốc`, `TOTAL_INCREASING`), `dynamic_water_goal` (`ml`, `MEASUREMENT`).
    - **Cafein & Cồn**: `current` (`mg`, `MEASUREMENT`), `consumed_today` (`mg`, `TOTAL_INCREASING`), `peak` (`mg`, `MEASUREMENT`), `caffeine_percent` (`%`, `MEASUREMENT`), `bac_level` (`%`, `MEASUREMENT`).
    - **Chỉ số Giấc ngủ**: `sleep_score` (`đ`, `MEASUREMENT`), `sleep_duration` (`h`, `DURATION`), `deep_sleep` (`h`, `DURATION`), `rem_sleep` (`h`, `DURATION`), `light_sleep` (`h`, `DURATION`), `awake_time` (`min`, `DURATION`), `sleep_efficiency` (`%`, `MEASUREMENT`).
    - **Sinh học & Môi trường**: `aggregated_steps` (`steps`, `TOTAL_INCREASING`), `aggregated_heart_rate` (`bpm`, `MEASUREMENT`), `weight` (`kg`, `WEIGHT`), `heat_index` (`°C`, `TEMPERATURE`).

---

## [2026.08.28.b1] - 2026-08-28

### 🐛 Sửa lỗi hiển thị phông chữ tiếng Việt (Mojibake Fixes)
- **Khắc phục triệt để lỗi vỡ chữ tiếng Việt**: Khôi phục và chuẩn hóa toàn bộ nội dung trong `strings.json` và `translations/vi.json` về chuẩn UTF-8 thuần (No BOM), sửa lỗi hiển thị các ký tự `Chá»%nh sá»a Há»" sÆ¡...` trên giao diện Home Assistant.

---

## [2026.08.27.b3] - 2026-08-27

### 🐛 Sửa lỗi Encoding (Bug Fixes)
- **Sửa lỗi không load được Config Flow do UTF-8 BOM (`unexpected character: line 1 column 1 (char 0)`)**: Loại bỏ hoàn toàn Byte Order Mark (BOM) khỏi các file `translations/en.json`, `translations/vi.json` và `strings.json`, đảm bảo file JSON thuần UTF-8 tương thích 100% với JSON parser của Home Assistant.

---

## [2026.08.27.b2] - 2026-08-27

### 🐛 Sửa lỗi tương thích & Tối ưu (Bug Fixes & Improvements)
- **Sửa lỗi không load được integration ("Not loaded")**: Khắc phục lỗi tương thích import `UTC` từ thư viện `datetime` trên môi trường Home Assistant Core/Python, chuyển sang chuẩn `timezone.utc`.
- **Chuẩn hóa toàn bộ mã nguồn sạch**: Làm sạch mã nguồn `utils/caffeine_calc.py` và `utils/alcohol_calc.py`, loại bỏ hoàn toàn các đoạn code nén `exec` để tăng tốc độ load và độ ổn định.

---

## [2026.08.27.b1] - 2026-08-27

### ✨ Tính năng mới (Features)
- **Bổ sung các Entity chỉ số giấc ngủ (Sleep Index Entities)**:
  - Tích hợp 8 chỉ số giấc ngủ trực tiếp vào **Bước 3/5: Cấu hình Cảm biến & Đồng bộ** (`environment`) cho từng thiết bị đeo thông minh (`Wearable 1`, `Wearable 2`, `Wearable 3`):
    - `wearable_{i}_sleep_score`: Cảm biến điểm số giấc ngủ (Sleep Score)
    - `wearable_{i}_sleep_duration`: Cảm biến thời lượng ngủ (Sleep Duration)
    - `wearable_{i}_sleep_deep`: Cảm biến thời gian ngủ sâu (Deep Sleep)
    - `wearable_{i}_sleep_rem`: Cảm biến thời gian ngủ REM (REM Sleep)
    - `wearable_{i}_sleep_light`: Cảm biến thời gian ngủ nông (Light Sleep)
    - `wearable_{i}_sleep_awake`: Cảm biến thời gian thức trong đêm (Awake Time)
    - `wearable_{i}_sleep_efficiency`: Cảm biến hiệu suất giấc ngủ (Sleep Efficiency %)
    - `wearable_{i}_sleep_state`: Cảm biến trạng thái giấc ngủ (Sleep State / Stage)
- **Tự động khởi tạo hệ thống cảm biến giấc ngủ trong Home Assistant**:
  - `sensor.mait_{person}_sleep_score`: Điểm số chất lượng giấc ngủ (icon `mdi:sleep`).
  - `sensor.mait_{person}_sleep_duration`: Tổng thời lượng ngủ (icon `mdi:bed-clock`).
  - `sensor.mait_{person}_deep_sleep`: Thời gian ngủ sâu (icon `mdi:power-sleep`).
  - `sensor.mait_{person}_rem_sleep`: Thời gian ngủ REM (icon `mdi:brain`).
  - `sensor.mait_{person}_light_sleep`: Thời gian ngủ nông (icon `mdi:weather-night`).
  - `sensor.mait_{person}_awake_time`: Thời gian thức trong đêm (icon `mdi:alarm-snooze`).
  - `sensor.mait_{person}_sleep_efficiency`: Hiệu suất giấc ngủ (đơn vị `%`, icon `mdi:chart-arc`).
  - `sensor.mait_{person}_sleep_state`: Trạng thái giấc ngủ thời gian thực.
  - `sensor.mait_{person}_sleep_summary`: Tổng quan đánh giá giấc ngủ kèm thuộc tính chi tiết (`extra_state_attributes`).
- **Tổng hợp thông minh từ thiết bị đeo (`coordinator.py`)**:
  - Tự động ưu tiên đọc dữ liệu giấc ngủ từ thiết bị đang đeo trên tay (`on_body == on`).
  - Tự động đưa các cảm biến giấc ngủ vào chu kỳ đánh thức/cập nhật dữ liệu từ ứng dụng di động (`update_entity`).
- **Bổ sung thuộc tính giấc ngủ vào `LastMedicineSensor`**:
  - Expose toàn bộ cấu hình và trạng thái cảm biến giấc ngủ vào danh sách `wearables` attribute.

### 🔧 Chuẩn hóa quy trình (Chores & Rules)
- Chuyển đổi định dạng phiên bản build sang quy chuẩn: `YYYY.MM.DD.bx`.
- Cập nhật quy tắc bắt buộc cập nhật Changelog, Version Manifest và đẩy GitHub tự động.

---

## [2.2.27] - 2026-07-14
- Hỗ trợ đồng bộ động nhiều thiết bị đeo (multi-device force sync).
- Tối ưu chu kỳ đồng bộ Companion App.

---

## [2.2.26] - 2026-07-13
- Hỗ trợ cấu hình tối đa 3 thiết bị đeo thông minh (Wearable 1, 2, 3) với cảm biến on-body, pin, và calo.
- Đồng bộ hóa bản dịch và phân vùng hiển thị trong Options Flow.

---

## [2.2.0] - 2026-07-06
- Tái cấu trúc toàn bộ quy trình thiết lập thành chuẩn 5 bước rõ ràng.
- Áp dụng nguyên tắc Single Source of Truth cho toàn bộ ngôn ngữ và thực thể tại `strings.json`.
