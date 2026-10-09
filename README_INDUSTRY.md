# Hướng Dẫn & Đặc Tả Kỹ Thuật Module Ngành (Người 2)

> **Dự án**: Hệ thống Phân tích Cơ hội Đầu tư Cổ phiếu MMB  
> **Hạn nộp**: 16:20 ngày 09/10/2026  
> **Người phụ trách**: Người 2 (Module Ngành - Industry Module)  
> **Hợp đồng dữ liệu**: Tuân thủ 100% chuẩn Input/Output V1 (JSON UTF-8, `schema_version="1.0"`)

---

## 1. Mục tiêu và Phạm vi Module

Module Ngành thực hiện đánh giá độc lập bức tranh vĩ mô của ngành và định vị doanh nghiệp trong tương quan với các đối thủ cạnh tranh cùng ngành (Peers):
1. **Phân loại ngành & chu kỳ**: Xác định mã ngành ICB, tên ngành, và giai đoạn chu kỳ ngành (Phục hồi / Mở rộng / Chững lại / Suy giảm).
2. **Nhóm doanh nghiệp so sánh (Peers Benchmarking)**: Lựa chọn 3-5 doanh nghiệp cùng ngành tiêu biểu; nêu rõ cơ sở so sánh (`comparison_basis`), vốn hóa thị trường và các chỉ số định giá (P/E, P/B, ROE, ROA, Net Margin, Debt/Equity, Revenue Growth).
3. **Chỉ số toàn ngành (Industry Metrics)**: P/E trung vị, P/B trung vị, ROE bình quân, biên lợi nhuận ròng bình quân, tốc độ tăng trưởng sản lượng/tiêu thụ.
4. **Nhận định & Luận điểm ngành (Findings)**: Đánh giá cung - cầu, rào cản gia nhập, lợi thế kinh tế nhờ quy mô (Moat) và tác động của chính sách chính phủ.
5. **Rủi ro ngành (Risks)**: Nhận diện biến động giá nguyên vật liệu, áp lực cạnh tranh nội địa/nhập khẩu và rủi ro chu kỳ kinh tế.
6. **Truy vết nguồn kiểm chứng (Sources)**: Mọi số liệu và nhận định đều có `evidence_refs` trỏ trực tiếp tới nguồn chính thống (Hiệp hội ngành VSA/VNBA/VINASA, Tổng cục Thống kê GSO, BCTC kiểm toán, Sở Giao dịch HSX/HNX).

---

## 2. Quy ước Số liệu & Dữ liệu (Strict Conventions)

| Quy ước | Chuẩn áp dụng | Ví dụ hợp lệ | Ví dụ vi phạm (Bị từ chối) |
| :--- | :--- | :--- | :--- |
| **Tiền tệ** | VND (số nguyên hoặc float) | `5820000000000.0` | `"5,820 tỷ VND"`, `"$250M"` |
| **Tỷ lệ / Tỷ suất** | Số thập phân (Float) | `0.142` (tức 14.2%) | `"14.2%"`, `14.2` |
| **Ngày tháng** | Chuỗi `YYYY-MM-DD` | `"2026-10-09"` | `"09/10/2026"`, `"2026/10/09"` |
| **Dữ liệu thiếu** | Giá trị `null` (None trong Python) | `null` | `0`, `""`, `"N/A"` |
| **Tiền tố nguồn** | Prefix `ind_src_` | `"ind_src_vsa_report_2026"` | `"src_01"`, `"vsa"` |
| **Ngày công bố nguồn** | `published_at <= as_of_date` | `published_at="2026-09-15"` | `published_at > as_of_date` |

---

## 3. Cách Tích hợp Cho Các Thành Viên Trong Nhóm

### Cho Người 5 (Điều phối & Giao diện):

Người 5 có thể gọi trực tiếp hàm Python trong cùng hệ thống hoặc chạy qua Command Line:

#### Cách 1: Gọi hàm Python (Khuyến nghị cho Web Streamlit / FastAPI)
```python
from industry.analyzer import analyze_industry

# Request từ form người dùng hoặc Orchestrator
request = {
    "schema_version": "1.0",
    "run_id": "run_20261009_140000",
    "ticker": "HPG",
    "exchange": "HOSE",
    "as_of_date": "2026-10-09",
    "period_start": "2025-01-01",
    "period_end": "2026-09-30",
    "investment_horizon": "Trung hạn 6 - 12 tháng"
}

# Nhận output industry.json chuẩn V1
industry_output = analyze_industry(request)
```

#### Cách 2: Chạy qua dòng lệnh (CLI)
```bash
# Phân tích cổ phiếu bất kỳ và xuất file industry.json
python -m industry.analyzer --ticker HPG --as-of-date 2026-10-09 -o industry.json

# Xuất khung rỗng pending để Người 5 test ghép nối luồng khi chưa nạp data thật:
python -m industry.analyzer --pending -o industry.json
```

---

### Cho Người 4 (Chiến lược đầu tư):
Người 4 đọc các khóa sau từ `industry.json` để đưa vào mô hình định giá:
- `data.industry_code`: Mã ngành ICB.
- `data.sector_cycle_stage`: Giai đoạn chu kỳ ngành để điều chỉnh P/E mục tiêu.
- `data.peers`: Mảng danh sách đối thủ để chạy mô hình định giá tương đối P/E và P/B trung vị (Relative Valuation).
- `data.metrics`: Lấy `ind_pe_median`, `ind_pb_median`, `ind_roe_avg` làm mốc tham chiếu so sánh sức khỏe doanh nghiệp.
- `data.risks`: Lấy danh sách rủi ro ngành để đưa vào kết luận rủi ro tổng hợp.

---

### Cho Người 6 (Xuất Báo Cáo PDF):
Người 6 hiển thị mục Phân tích Ngành trên PDF:
- Bảng Ma trận so sánh Doanh nghiệp cùng ngành (Peers Benchmarking Table): Ticker, Vốn hóa, P/E, P/B, ROE, Biên LN.
- Đoạn tóm tắt Chu kỳ & Triển vọng ngành từ `data.findings`.
- Hộp cảnh báo Rủi ro ngành từ `data.risks`.
- Bảng trích dẫn Nguồn kiểm chứng từ `sources`.

---

## 4. Chạy Kiểm Thử (Unit Tests)

Chạy bộ test tự động kiểm tra 100% hợp đồng dữ liệu:
```bash
python -m unittest discover -s industry/tests
```
Tất cả 5 test cases đều kiểm tra nghiêm ngặt tính hợp lệ của schema, kiểu dữ liệu, các phép truy vết bằng chứng (evidence cross-reference) và quy ước số.
