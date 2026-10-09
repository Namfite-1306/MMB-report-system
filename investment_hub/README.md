# MMB Analysis — hệ thống tích hợp của nhóm

Ứng dụng local ghép ba module dữ liệu, chiến lược đầu tư và bộ xuất PDF. Giao diện
HTML/CSS/JavaScript thuần; máy chủ Node.js dùng thư viện chuẩn, không cần `npm install`.
Chọn Node.js vì workspace đã có Node, tránh cài thêm framework trong thời hạn nhóm.
Hệ thống nhận module Python hoặc JavaScript và JSON theo hợp đồng v1.0 trong Google Sheets.

## Chạy

Yêu cầu Node.js 20 trở lên (đã kiểm tra bằng Node 24.17.0), Python 3.10+.
Sau khi clone repo, cài dependency Python và cài năm module lần đầu:

```powershell
cd investment_hub
python -m pip install -r "PDF Format/report/requirements.txt"
node scripts/install-team.mjs
node scripts/install-pdf.mjs
npm start
```

Hoặc mở `start.cmd`. Vào `http://127.0.0.1:3000`. Ctrl+C để dừng.
Máy chủ chỉ lắng nghe loopback. Nếu cổng đã dùng: `$env:PORT='3001'; npm start`.
Chưa thiết kế cho hosting công khai, đăng nhập hay nhiều người dùng đồng thời trên mạng.

Module Python cần Python 3.10+ và dependency của thành viên trên máy chạy.
Nếu `python` không chạy được, đặt `$env:PYTHON_BIN='đường dẫn đầy đủ tới python.exe'` trước `npm start`.
Không ghi đường dẫn cá nhân cố định vào mã nguồn.

## Cách dùng

**Người 1–4 và PDF người 6 đã cài:** tạo input rồi bấm **Chạy workflow & tạo PDF**.
Không cần nhập mã ngành; hệ thống tra theo bản ánh xạ ticker của người 2. Tên ngành
có thể để trống để tự điền. Mã chưa được ánh xạ ghi rõ Chưa phân loại.
Tab Dashboard có giá/MA20, khối lượng, doanh thu/LNST/CFO và bộ lọc thời gian.
Biểu đồ cũng xuất trong HTML và PDF; PDF hiển thị toàn kỳ phân tích.
Nút sáng/tối nằm trên thanh đầu trang và lưu lựa chọn trên máy. Có thể mở lần HPG
đã chạy từ danh sách để tải PDF ngay. Xem [workflow và giới hạn dữ liệu](docs/team-workflow.md).

1. Nhập mã, sàn, ngành, ngày chốt, khoảng phân tích, thời hạn. Tạo lần phân tích.
2. Tải `request.json`, gửi cùng file này cho người 1–4. `run_id` do hệ thống tạo.
3. Tải lên `macro.json`, `industry.json`, `company.json` ở đúng ô. Hệ thống kiểm
   định danh, kiểu số, ngày, nguồn và cấu trúc. JSON lệch `run_id` bị từ chối, không tự sửa.
4. Tải `strategy.json` sau dữ liệu, hoặc cài/chạy module người 4. Đổi bất kỳ module
   dữ liệu nào sẽ đưa chiến lược về pending và vô hiệu PDF cũ, tránh kết luận lỗi thời.
5. Tải `analysis.json`, hoặc mở báo cáo để In / Lưu PDF bằng trình duyệt.
6. Module PDF người 6 đã tích hợp. Bấm Tạo PDF bằng module → Tải PDF.

Đóng gói/cài lại PDF sau khi sửa: `node scripts/install-pdf.mjs`. Nguồn tại
`PDF Format/report/`; gói bàn giao tại `packages/pdf.module.json`. Renderer dùng
ReportLab và font tiếng Việt nhúng. Python ưu tiên `PYTHON_BIN`, sau đó runtime
Codex nếu có, cuối cùng PATH. Xem `PDF Format/report/README.md` để chuyển máy.

`Tải cấu trúc` xuất envelope hiện tại của module; lúc mới tạo chỉ có mảng rỗng,
null/pending và cảnh báo. Không có dữ liệu nghiên cứu, chiến lược hay kết quả đầu tư giả.

## Cấu trúc

```text
investment_hub/
  server.mjs               API, lưu phiên phân tích, điều phối
  lib/contracts.mjs        kiểm hợp đồng và điều kiện sử dụng kết luận
  lib/plugins.mjs          cài/chạy module của nhóm
  lib/report.mjs           báo cáo HTML để xem/in
  public/                  giao diện cơ bản, chỉnh tại đây
  templates/run.py          skeleton module Python, chưa có logic
  templates/run.mjs         skeleton module JavaScript, chưa có logic
  scripts/package-module.mjs công cụ đóng gói bàn giao
  tests/                   unit/integration tests
  modules/                 phiên bản code cài bởi nhóm (tạo khi upload)
  storage/runs/<run_id>/    input, output, PDF (tạo khi sử dụng)
```

Mỗi lần phân tích có request.json, bốn envelope và analysis.json. Bản module cài
mới lưu phiên bản riêng. JSON được ghi bằng tệp tạm rồi đổi tên. Không có database.
Tên thành viên, ngày chốt, dữ liệu và output thực tế được nhập khi sử dụng.

## Chạy module tự động

Module có entrypoint `run.py` hoặc `run.mjs`, nhận **một JSON từ stdin**, trả
**một JSON ra stdout**; đưa log sang stderr. Thời gian tối đa 120 giây/module.

Input người 1–4:

```text
{ "request": <request.json>, "modules": { "macro": <envelope>,
  "industry": <envelope>, "company": <envelope>, "strategy": <envelope> } }
```

1–3 dùng request và lấy nguồn riêng; 4 đọc cả ba envelope. Output là envelope module
đúng schema. Nút chạy toàn bộ gọi **1–3 song song**, sau đó gọi 4 trên dữ liệu đã nhận.
Module chưa cài được bỏ qua, JSON upload trước đó được giữ. Chạy lỗi trả nhật ký,
không ghi đè output hợp lệ bằng kết quả sai. Có thể chạy riêng mỗi module.

Đóng gói ở thư mục ứng dụng:

```powershell
node scripts/package-module.mjs strategy "D:/module_cua_thanh_vien" run.py strategy.module.json
```

Upload `strategy.module.json` ở phần Cài module. Đánh dấu tin cậy mã nguồn; chỉ
chạy khi bấm nút chạy. Gói gồm mã/text, không hỗ trợ ZIP, binary, file dữ liệu lớn
hoặc cài dependency tự động. Dữ liệu lớn để tại nguồn/module đọc qua cấu hình phù hợp.
Gói module tối đa 8 MB nội dung text, 100 file. Không nạp code trong upload dữ liệu.

## Hợp đồng dữ liệu thực thi

Input chung: schema_version=1.0, run_id, ticker viết hoa, exchange=HOSE/HNX/UPCOM,
industry_code/name, as_of_date, period_start/end (YYYY-MM-DD), investment_horizon,
language=vi, currency=VND. Khoảng phân tích không vượt ngày chốt.

Mọi envelope cần: schema_version, run_id, module, ticker, as_of_date, generated_at
(ISO8601 có múi giờ), status=pending/ok/partial/error, data, sources, warnings, errors.

- Source: source_id (prefix `macro:`/`industry:`/`company:`/`strategy:`), title, url HTTP(S),
  published_at (ngày/timestamp hoặc null), retrieved_at, locator (chuỗi/null),
  publication_date_verified (boolean). Cờ verified là xác nhận của người cung cấp,
  hệ thống không tự kiểm nội dung website nguồn.
- Metric: metric_id có prefix module, value số/null, unit, frequency, period_start,
  period_end, source_refs mảng ID nguồn tồn tại, formula_id chuỗi/null.
- Macro/industry/company: data.metrics/findings/risks là mảng. Findings và risks
  gồm text và evidence_refs tới source_id/metric_id trong module.
- Industry: thêm industry_code khớp input và peers[].
- Company: thêm price_series[] (date,close,volume,adjustment_basis,source_refs) và
  financials[] (item_id,value,unit,period_start,end,statement_scope,source_refs).
- Strategy: data.theory_sources[], rules[], risks[], evidence_refs[], conclusion.
  Conclusion gồm label=attractive/watchlist/unattractive/insufficient_data, rationale,
  evidence_refs và horizon khớp input. Kết luận đủ điều kiện cần lý thuyết/quy tắc/bằng chứng.

Số tiền VND, shares cho số cổ phiếu, tỷ lệ thập phân (0.12 tương ứng 12%), thiếu dùng null.
Định nghĩa công thức, kỳ quý/năm/TTM, hợp nhất/riêng lẻ và corporate actions do
module chuyên môn ghi; người 5 không sửa số hoặc tính lại chỉ số của thành viên.

Nguồn chưa xác minh ngày hoặc công bố sau ngày chốt không đủ điều kiện làm bằng
chứng. Hệ thống giữ nguyên envelope gốc và tạo `display_conclusion` an toàn,
`conclusion_usable` cùng warnings/errors. **PDF phải dùng display_conclusion**,
không dùng kết luận raw trong modules.strategy khi không đủ điều kiện.
Phân tích có pending/error/nguồn chưa đủ điều kiện không trở thành ok. Không có backtest.

## Hợp đồng module PDF người 6

Stdin: `{ "analysis": <analysis.json>, "output_dir": <thư mục tuyệt đối do hệ thống cấp> }`.
Module viết `report.pdf` vào output_dir, stdout trả:

```text
{ "pdf_filename": "report.pdf", "manifest": {
  "schema_version": "1.0", "run_id": <analysis.run_id>,
  "ticker": <analysis.request.ticker>, "as_of_date": <analysis.request.as_of_date>,
  "overall_status": <analysis.overall_status>, "generated_at": <ISO8601>,
  "sections_present": ["macro","industry","company","strategy","risks","sources"],
  "warnings": <danh sách cảnh báo>, "pdf_filename": "report.pdf"
} }
```

Không gọi module PDF tự động khi chỉ upload dữ liệu. Nút Tạo PDF gọi rõ ràng.
Máy chủ kiểm manifest, đường dẫn và header/EOF PDF; chưa xác minh được toàn bộ
nội dung/layout của PDF thành viên. Người 6 vẫn phải kiểm font Việt và số liệu.
Báo cáo HTML và PDF trình bày chỉ số, nhận định, rủi ro, nguồn, kết luận và dashboard
giá/MA20, khối lượng, BCTC. Chi tiết toàn bộ chuỗi nằm trong analysis.json.

## Kiểm thử

```powershell
npm test
node --check server.mjs
node --check public/app.js
```

Test dùng dữ liệu cấu trúc tổng hợp chỉ để kiểm phần mềm, không phải dataset nghiên cứu.
Kiểm định danh, ngày, null, provenance, stale strategy, package traversal, chạy
module, upload, pipeline và đường tải tệp. Không xác nhận mô hình đầu tư có hiệu quả.

## Cài đặt và cập nhật module

Mã nguồn, package và snapshot HPG công khai đã được đưa vào repo. Storage và phiên
bản module đã cài không được commit; hai lệnh install ở trên tái tạo chúng trên máy mới.
install-team mặc định đọc người 1/2/4 từ thư mục gốc repo ở ngay trên investment_hub;
có thể truyền đường dẫn repo khác làm đối số khi cập nhật nguồn bàn giao.
Người 1–4 dùng cùng request.json, không tự tạo run_id khác. Người 6 dùng đúng
analysis.json và hợp đồng PDF phía trên.
