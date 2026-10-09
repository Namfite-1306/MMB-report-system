# Module 1 — Vĩ mô

Module tạo `macro.json` và, khi được yêu cầu, `macro_data.xlsx` cho hệ thống phân tích cơ hội đầu tư cổ phiếu trên HOSE, HNX và UPCoM. Module cung cấp bối cảnh vĩ mô và cơ chế tác động có điều kiện; không chấm điểm doanh nghiệp, dự báo giá hoặc đưa khuyến nghị mua/bán.

## Cấu trúc

- `macro_module/core.py`: kiểm tra input, lọc dữ liệu theo ngày chốt, tạo tóm tắt và tác động ngành.
- `generate_macro.py`: CLI tạo JSON và tùy chọn xuất Excel từ cùng một kết quả trong bộ nhớ.
- `tools/build_macro_excel.mjs`: dựng workbook bằng Artifact Tool; không chứa bộ số liệu riêng.
- `data/verified_macro_data.json`: snapshot dữ liệu cục bộ đã kiểm chứng, không phải crawler.
- `config/industry_mapping.json`: ánh xạ ngành có thể chỉnh sửa.
- `examples/input.sample.json`: input mẫu; `schema_version` và `run_id` do bên gọi truyền vào.
- `macro.json`, `macro_data.xlsx`: đầu ra chạy thử.
- `tests/test_macro_module.py`: kiểm tra hợp đồng, chất lượng nguồn, dữ liệu thiếu và ngành chưa ánh xạ.

## Lệnh chạy

Từ thư mục `macro-module`, tạo đồng thời JSON và Excel với đầy đủ input chung:

```powershell
python generate_macro.py `
  --input examples/input.sample.json `
  --data-file data/verified_macro_data.json `
  --industry-map config/industry_mapping.json `
  --output macro.json `
  --excel-output macro_data.xlsx `
  --node-command "C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" `
  --force
```

`--force` là xác nhận rõ ràng cho phép ghi đè. Nếu bỏ tùy chọn này, CLI từ chối khi bất kỳ output đích nào đã tồn tại. Cách chạy JSON cũ vẫn tương thích:

```powershell
python generate_macro.py `
  --input examples/input.sample.json `
  --data-file data/verified_macro_data.json `
  --industry-map config/industry_mapping.json `
  --output macro.local.json
```

`generate_macro.py` **không tải dữ liệu mới**. Mỗi lần chạy chỉ tái tạo output từ snapshot cục bộ `data/verified_macro_data.json`; metadata ghi `refresh_behavior=local_snapshot_only_no_network_fetch` và `network_fetch_performed=false`.

Xuất Excel cần Node.js và package `@oai/artifact-tool`. Trong Codex Desktop, có thể nối `node_modules` của module với runtime bundle bằng junction (không commit junction):

```powershell
New-Item -ItemType Junction `
  -Path node_modules `
  -Target "C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules"
```

Chạy kiểm tra:

```powershell
python -m unittest discover -s tests -v
```

## Hợp đồng input

Tám trường bắt buộc:

```json
{
  "schema_version": "1.0.0",
  "run_id": "sample-run-20250106-001",
  "ticker": "FPT",
  "exchange": "HOSE",
  "industry": "Công nghệ thông tin",
  "as_of_date": "2025-01-06",
  "analysis_period": {
    "start_date": "2024-01-01",
    "end_date": "2025-01-06"
  },
  "investment_horizon": {
    "label": "trung_han",
    "months": 18
  }
}
```

Adapter yêu cầu `analysis_period.start_date` và `analysis_period.end_date` theo `YYYY-MM-DD`; ngày kết thúc không sau `as_of_date`. `investment_horizon` nhận chuỗi hoặc object. Nếu là object, `months <= 6` là ngắn hạn, `7-24` là trung hạn và trên `24` là dài hạn. Giá trị gốc được giữ trong `data.metadata.input`.

Module không tự sinh hoặc thay đổi `schema_version`, `run_id`, `ticker` và `as_of_date`.

## Hợp đồng output và ý nghĩa status

Các trường top-level luôn có: `schema_version`, `run_id`, `ticker`, `as_of_date`, `status`, `data`, `sources`, `warnings`, `errors`.

- `ok`: không có cảnh báo chất lượng ảnh hưởng status.
- `partial`: kết quả dùng được nhưng có ít nhất một cảnh báo được đánh dấu `affects_status=true`, ví dụ dữ liệu bắt buộc bị thiếu, ngày chốt vượt phạm vi snapshot, ngành chưa ánh xạ hoặc một nguồn chịu quy ước chất lượng cần xác minh thêm.
- `error`: input hoặc dataset không hợp lệ, khiến module không thể tạo phân tích bình thường.

Nguồn thứ cấp **không mặc định** làm status thành `partial`. Quyết định phụ thuộc `quality_treatment` của từng nguồn. Trong bộ mẫu, nguồn TTXVN cho tỷ giá có `quality_treatment=partial_until_primary_verified`, nên `status=partial` do quy ước chất lượng nguồn và thiếu URL lịch sử trực tiếp ổn định từ NHNN — không phải vì giá trị tỷ giá bị thiếu hoặc chưa đọc được.

Quy ước dữ liệu:

- Tỷ lệ lưu dạng thập phân: `0.045` tương ứng `4,5%`.
- Tỷ giá trung tâm dùng `VND/USD`; không trộn với giá mua/bán.
- Dữ liệu thiếu là `null` trong JSON và ô trống trong Excel; không dùng `0` thay thế.
- Bộ ghi JSON cấm `NaN` và `Infinity`.
- Quan sát chỉ được chọn khi ngày công bố của quan sát và nguồn không muộn hơn `as_of_date`.
- `macro_summary.observations` là số liệu quan sát; `calculated_results` là phép tính; `assessment` và `industry_impacts` là nhận định/giả định.

## Workbook Excel

`macro_data.xlsx` được dựng từ đúng object kết quả đã dùng để ghi `macro.json`:

- `Macro_Data`: mỗi dòng một quan sát; số liệu là kiểu số, tỷ lệ hiển thị phần trăm, tỷ giá hiển thị số nguyên, ngày theo `YYYY-MM-DD`, có trạng thái/ghi chú cho dữ liệu thiếu.
- `Sources`: nguồn, URL, kỳ dữ liệu, ngày công bố, ngày truy cập, phân loại và quy ước chất lượng.
- `Analysis`: input/metadata lần chạy, status và lý do, tóm tắt, tác động ngành, cơ hội/rủi ro, warnings, errors và limitations.

Cả ba sheet có tiêu đề dễ đọc và bộ lọc bảng. Ngày công bố, ngày hiệu lực và ngày truy cập là ba khái niệm riêng; không thay thế lẫn nhau.

## Dữ liệu đã xác minh trong snapshot

Snapshot chỉ được xác minh đến **2025-01-06** và không được trình bày là dữ liệu hiện tại. Ngày truy cập nguồn là `2026-10-09`:

1. GDP thực năm 2024 tăng `0.0709` so với năm trước và CPI bình quân năm 2024 tăng `0.0363`, công bố ngày `2025-01-06` bởi Tổng cục Thống kê: <https://www.nso.gov.vn/du-lieu-va-so-lieu-thong-ke/2025/01/thong-cao-bao-chi-tinh-hinh-kinh-te-xa-hoi-quy-iv-va-nam-2024/>.
2. Lãi suất tái cấp vốn giảm từ `0.05` xuống `0.045`/năm, quyết định công bố ngày `2023-06-16`, hiệu lực `2023-06-19`, nguồn NHNN: <https://sbv.gov.vn/vi/w/sbv570036>.
3. Tỷ giá **trung tâm** ngày `2025-01-06` là số nguyên `24337 VND/USD`. Cách viết `24.337` trong tiêu đề TTXVN dùng dấu chấm phân cách hàng nghìn, không phải dấu thập phân: <https://infographics.vn/interactive-ty-gia-trung-tam-ngay-6-1-2025-1-usd-24337-vnd/214098.vna>.

Không có quan sát nào trong đầu ra mẫu được công bố sau ngày chốt `2025-01-06`.

## Dùng chung cho nhiều mã và phạm vi ngành

`data.metadata.dataset.cache_key` chỉ phụ thuộc `as_of_date`, `dataset_id` và `dataset_version`, không phụ thuộc ticker. Module điều phối có thể nạp snapshot một lần cho nhiều mã cùng ngày chốt; phần tác động được tạo riêng theo ngành.

Ánh xạ hiện có chỉ bao phủ **5 nhóm**: công nghệ, ngân hàng, bất động sản, sản xuất xuất khẩu và tiêu dùng/bán lẻ. Ngành ngoài phạm vi trả bối cảnh chung cùng cảnh báo `INDUSTRY_MAPPING_NOT_FOUND`; module không đoán ngành từ mã.

Ví dụ gọi trong Python:

```python
from macro_module import build_macro_result, load_json

payload = load_json("examples/input.sample.json")
dataset = load_json("data/verified_macro_data.json")
mapping = load_json("config/industry_mapping.json")
result = build_macro_result(payload, dataset, mapping)
```

## Điểm tích hợp Module 5 và Module 6

Module 5 nối theo `run_id`, kiểm tra `schema_version`, `status`, `warnings`, `errors` và dùng `data.metadata.dataset.cache_key` để tái sử dụng dữ liệu. Không chuyển tác động có điều kiện thành tín hiệu mua/bán.

Module 6 (PDF) dùng:

1. `data.metadata.input`, `actual_data_periods` và `status_details` cho phần phạm vi/phương pháp.
2. `data.indicators` cùng `sources` cho bảng số liệu và chú thích nguồn.
3. `data.macro_summary.observations`, `calculated_results`, `assessment` để tách số liệu, phép tính và nhận định.
4. `data.industry_impacts`, `opportunities`, `risks` cho nội dung ngành.
5. `data.limitations`, `warnings`, `errors` cho lưu ý cuối báo cáo.

## Giới hạn hiện tại

- Snapshot lịch sử không phải chuỗi thời gian, không tự làm mới và chỉ xác minh đến `2025-01-06`.
- Chưa có URL NHNN trực tiếp ổn định cho tỷ giá lịch sử ngày mẫu; nguồn TTXVN chịu quy ước `partial_until_primary_verified`.
- Chỉ có năm nhóm ngành nêu trên; chưa tuyên bố hỗ trợ đầy đủ mọi mã/ngành.
- Chưa xác minh point-in-time cho các bản GDP/CPI điều chỉnh sau lần công bố ban đầu; module loại bản công bố sau ngày chốt thay vì hồi tố.
- Không có collector trực tuyến, giao diện, backtest, ML hoặc tối ưu danh mục.
