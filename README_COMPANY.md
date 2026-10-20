# Module doanh nghiệp - Thành viên 3

Bám Sheet 1 **Phan cong 6 nguoi** và tab **Input Output chung** trong kế hoạch nhóm. Chỉ thực hiện thu thập, chuẩn hóa, đối chiếu và phân tích dữ liệu doanh nghiệp. Người 4 sở hữu kết luận đầu tư; người 5 điều phối; người 6 xuất PDF.

## Chạy ngay bản HPG đã đối chiếu

Python **3.10+**, không cần cài package ngoài. Giải nén gói bàn giao vào thư mục gốc repo `MMB-report-system` để có `company/` cạnh `industry/`.

```bash
python -m company.analyzer --request company/examples/request.hpg.json --snapshot company/examples/hpg_raw --verified-bundle company/examples/hpg_verified.json -o company.json
python -m unittest discover -s company/tests -v
```

Lệnh thứ nhất chạy hoàn toàn offline, đọc snapshot thật. `company.json` dùng số 6 tháng đầu năm 2026 (`financial_basis=ytd`); bảng cân đối tại 30/06/2026. `period_end=2026-10-08` vì lúc thu thập ngày 09/10 chưa kết thúc phiên. `as_of_date=2026-10-09`. Thời hạn 6–12 tháng trong request là **cấu hình chạy thử**, cần thay theo yêu cầu người dùng của nhóm.

Bản FY2025 đã đối chiếu được giữ riêng:

```bash
python -m company.analyzer --request company/examples/request.hpg.annual.json --snapshot company/examples/hpg_raw --verified-bundle company/examples/hpg_verified.json -o company/examples/company.hpg.annual.json
```

Không đổi run_id để ghép với `industry.json` hiện có một cách tùy tiện: người 5 tạo **một request chung** rồi chạy lại tất cả module. Hai file ví dụ annual/YTD là hai cách xem cùng bộ dữ liệu, không phải hai module để ghép vào cùng output.

## Lấy lại dữ liệu thật qua mạng

```bash
python -m company.analyzer --request request.json --raw-dir company/raw/run_moi --verified-bundle company/examples/hpg_verified.json -o company.json
```

`raw-dir` phải là thư mục mới. Bộ lấy dữ liệu gọi API công khai của Vietcap, tối đa 3 yêu cầu đồng thời, timeout có cấu hình, không vượt chặn truy cập hoặc tự tạo dữ liệu khi lỗi. Mỗi đáp ứng được lưu nguyên bytes kèm URL, POST body, ngày tải và SHA256. Nếu API đổi cấu trúc/lỗi, JSON báo `partial`/`error` cụ thể. Các endpoint được khảo sát ngày 09/10/2026; không bảo đảm chúng luôn hoạt động về sau.

Với **mã khác HPG**, đổi đủ input và bỏ bundle HPG:

```bash
python -m company.analyzer --request request.json --raw-dir company/raw/run_moi -o company.json
```

Khi chưa có BCTC được đối chiếu cho mã đó, dữ liệu API được giữ trong `data.financial_candidates`, chỉ số thiếu bằng chứng giữ `null`. `data.financials` chứa bản chuẩn hóa đã kiểm scope. Module không có cơ sở dữ liệu BCTC đã kiểm cho mọi mã. Bank/chứng khoán/bảo hiểm không dùng mapping hoặc hệ số thanh khoản của doanh nghiệp công nghiệp như thể chúng tương đương.

## Hàm người 5 gọi

```python
from company import analyze_company

company_output = analyze_company(
    request,  # đúng request chung, giữ schema_version/run_id/ticker/as_of_date
    raw_dir=f"company/raw/{request['run_id']}_{request['ticker']}",
    verified_bundle="company/examples/hpg_verified.json" if request["ticker"] == "HPG" else None,
)
```

Để tái lập không gọi mạng, truyền `snapshot_dir` thay `raw_dir`. `pending=True` trả khung đủ khóa, mảng trống, không tạo số hoặc nhận định giả. `validate_company_output` trong `company/contract.py` trả `(is_valid, errors)` cho người 5.

### Input bắt buộc

`schema_version="1.0"`, `run_id`, `ticker` viết hoa, `exchange` (HOSE/HNX/UPCOM), `industry_code`, `industry_name`, `as_of_date`, `period_start`, `period_end`, `investment_horizon`, `language="vi"`, `currency="VND"`.

Người 5 chốt ngành theo cùng hệ phân loại với người 2. Module giữ nguyên ngành/sàn của request và cảnh báo rằng chưa xác minh độc lập. Ngày thật hợp lệ; `period_start <= period_end <= as_of_date`; không nhận ngày chốt tương lai.

Hai input mở rộng **không đổi schema_version**: `financial_basis` (`annual`, `ytd`, `quarterly`, `ttm`; mặc định annual) và `statement_scope` (`consolidated`, `separate`; mặc định consolidated). Nên truyền rõ. Bộ dữ liệu HPG bàn giao có annual và YTD đã kiểm; chưa có bốn quý standalone đã kiểm để tính TTM.

## Quy ước tên và công thức chốt cho người 4/5/6

`data.metrics` là **mảng object**, không phải dictionary. Tra bằng `metric_id`. Các tỷ lệ giữ thập phân, PDF mới nhân 100 khi hiển thị %. `x` là số lần, không nhân 100. Tiền VND; EPS/giá VND/share; khối lượng shares. Tất cả tên có prefix `company_`.

| metric_id | Công thức / ý nghĩa | Điều kiện |
|---|---|---|
| company_revenue | Doanh thu **thuần** | Không dùng doanh thu trước giảm trừ |
| company_net_profit | LNST toàn tập đoàn | Cùng scope/kỳ |
| company_parent_profit | LNST thuộc cổ đông công ty mẹ | Tách cổ đông không kiểm soát |
| company_cfo | Lưu chuyển tiền thuần từ HĐKD | Cùng kỳ với lợi nhuận |
| company_basic_eps | EPS cơ bản **báo cáo** | Không suy EPS từ số cổ phiếu cuối kỳ; không cộng EPS quý |
| company_gross_margin | LN gộp / doanh thu thuần | Doanh thu > 0 |
| company_net_margin | LNST toàn tập đoàn / doanh thu thuần | Doanh thu > 0 |
| company_roa | LNST toàn tập đoàn / ((TS đầu kỳ + TS cuối kỳ)/2) | Có đúng hai mốc; không thay bằng cuối kỳ |
| company_roe | LN cổ đông mẹ / bình quân (VCSH tổng − lợi ích CĐ không kiểm soát) | Có số đầu/cuối kỳ; vốn bình quân > 0 |
| company_cfo_to_profit | CFO / LNST toàn tập đoàn | LNST > 0; không coi doanh nghiệp lỗ là tỷ số tốt |
| company_free_cash_flow | CFO + dòng chi mua sắm/xây dựng tài sản dài hạn | CAPEX cash mang dấu âm; FCF theo quy ước cash, không gọi là FCFF |
| company_revenue_growth_yoy | DT kỳ này / DT cùng kỳ năm trước − 1 | Cùng annual/YTD/quý và scope; nền > 0 |
| company_parent_profit_growth_yoy | LN cổ đông mẹ kỳ này / cùng kỳ − 1 | Nền > 0; nền lỗ/0 giữ null |
| company_current_ratio | TSNH / nợ ngắn hạn | Doanh nghiệp phi tài chính |
| company_quick_ratio | (TSNH − tồn kho) / nợ ngắn hạn | Đây là định nghĩa nhóm, vẫn chứa tài sản trả trước; không gọi là cash ratio |
| company_liabilities_to_assets | Tổng nợ phải trả / tổng tài sản | Không nhầm nợ phải trả với nợ vay |
| company_debt_to_equity | (Vay và nợ thuê tài chính ngắn + dài hạn) / tổng VCSH | Không dùng tổng nợ phải trả làm tử số |
| company_net_debt | Vay/nợ thuê tài chính ngắn + dài − tiền và tương đương | Không tự trừ tiền gửi có kỳ hạn |
| company_close | Close phiên hoàn chỉnh gần nhất theo nguồn | Ghi adjustment_basis; không thay phiên đang giao dịch bằng close |
| company_avg_volume_20 | Trung bình khối lượng 20 phiên có dữ liệu | Không lấp ngày nghỉ bằng 0 |
| company_pe | Giá / EPS annual hoặc TTM | EPS và giá cùng cơ sở cổ phiếu đã kiểm tới phiên; EPS > 0 |
| company_market_cap | Giá spot × cổ phiếu lưu hành có hiệu lực tại phiên | Không lấy vốn điều lệ/mệnh giá thay cổ phiếu lưu hành |
| company_pb | Vốn hóa / VCSH cổ đông mẹ gần nhất đã công bố | Vốn mẹ > 0; ghi kỳ book và phiên market riêng |

ROA/ROE `ytd` phản ánh **sáu tháng**, không phải tỷ suất cả năm; không nhân 2. Margin/growth dùng kỳ trong từng metric. Các hệ số balance dùng snapshot cân đối mới nhất đã xác minh, có thể khác kỳ annual; tuyệt đối đọc `period_start/end/frequency` khi so peer. P/E FY2025 không được đổi tên thành P/E TTM.

TTM chỉ cộng bốn quý **standalone liên tiếp đã kiểm**. Không cộng YTD, không cộng các báo cáo annual, không cộng EPS quý. Thiếu lịch sử hoặc bằng chứng kỳ/scope → null.

## Dữ liệu gốc và dữ liệu đã xử lý

- `company/examples/hpg_raw/`: 6 endpoint JSON gốc, metadata từng lần tải, 2 PDF issuer và trang lịch công bố issuer.
- `hpg_verified.json`: 66 dòng chuẩn hóa đọc từ PDF; không có số minh họa. Mỗi dòng có record_id, item_id, value, unit, frequency, kỳ, scope, verified và nguồn.
- `build_hpg_verified.py`: bản chép lại có thể tái tạo bundle từ **số đã đọc và kiểm ảnh PDF**; đây không phải OCR tự động cho mọi doanh nghiệp.
- `hpg_reconciliation.json`: đối chiếu 64 dòng có thể so cùng định nghĩa API/PDF; EPS YTD được bỏ khỏi phép cộng quý.
- `company.json`: envelope của người 3 cho tích hợp; luôn đủ `status/data/sources/warnings/errors`.

Ngày công bố kiểm từ lịch issuer; ngày ký báo cáo/ngày tải không thay thế ngày công bố. Vietcap publicDate và ngày issuer có thể khác nhau; giữ cả hai bằng chứng. Các snapshot API lịch sử có thể đã restate: không tự coi số tải hôm nay là số đã biết ở ngày chốt quá khứ.

### Cách nạp BCTC của mã khác hoặc repo miner

Xuất JSON theo cấu trúc `hpg_verified.json`, đổi `ticker`, không tái dùng nguồn HPG. Đối chiếu từng item, kỳ, đơn vị, scope, ngày công bố và vị trí PDF. Chỉ đặt `verified=true` khi đã kiểm; `publication_date_verified=true` cần bằng chứng ngày công bố. `record_id`/`source_id` phải duy nhất, có prefix `company_`. Tiền tỷ phải nhân 1e9 trước khi nạp; thiếu để null.

Đối với số cổ phiếu: `item_id=shares_outstanding`, `unit=shares`, `frequency=point_in_time`, `period_start=period_end` là ngày hiệu lực; thêm `valid_through` đã đối chiếu tới phiên định giá. Đối với EPS dùng P/E: thêm `per_share_basis_verified=true`, `share_basis_valid_through` và nguồn điều chỉnh cổ phiếu. Giá được đối chiếu thêm `basis_verified=true` và `adjustment_basis=unadjusted` hoặc `adjusted_to_latest_session`.

Không lấy công thức hay chỉ số miner làm bằng chứng mặc định. Module này tính lại công thức từ các dòng tài chính đã kiểm. Bộ kiểm tra không thể tự chứng minh một cờ verified do người nhập có đúng sự thật hay không; cần giữ PDF/URL và bảng đối chiếu.

## Phần người 6 cần hiển thị

Bảng metric: tên, giá trị, đơn vị, tần suất/kỳ. Hiển thị `null` là **Chưa đủ dữ liệu**, không phải 0. Sources: URL, ngày công bố, kỳ, locator. Tách annual và sáu tháng; giữ cảnh báo P/E/P/B/vốn hóa chưa xác minh. Chart giá phải ghi **chuỗi điều chỉnh theo nhà cung cấp, cơ sở điều chỉnh chưa xác minh**; không coi đây là lợi suất đầu tư hay dữ liệu backtest đã kiểm.

## Bàn giao và nghiệm thu

`company/docs/HANDOFF.md` ghi kết quả và vướng mắc hiện tại. `company/docs/SOURCES.md` ghi endpoint/tài liệu kỹ thuật. Chạy đối chiếu:

```bash
python -m company.reconcile --raw-dir company/examples/hpg_raw --verified-bundle company/examples/hpg_verified.json -o company/examples/hpg_reconciliation.json
```

Người 3 đã kiểm số JSON; soát số trên PDF nhóm **T+135** chỉ làm được sau khi người 6 xuất bản thật. Không đánh dấu nghiệm thu PDF thay người 6.

Hai schema máy đọc nằm tại `company/request.schema.json` và `company/company.schema.json`. Schema kiểm hình dạng dữ liệu; `company/contract.py` kiểm thêm ngày thật, số hữu hạn, khóa nguồn/bằng chứng, cắt ngày chốt và tính nhất quán tham chiếu. Nhóm không cần cài `jsonschema` để chạy module.

Sau khi review, để đưa phần người 3 lên repo nhóm, chỉ chọn `README_COMPANY.md`, `company/` và `company.json`; giữ module người khác nguyên trạng. Thư mục `__pycache__` không thuộc gói bàn giao.

Gói không sửa module của thành viên khác, không có giao diện, không quyết định mua/bán, không xuất báo cáo PDF. Nhóm tự review/copy files rồi push GitHub; chưa push/merge trong lượt làm việc này.
