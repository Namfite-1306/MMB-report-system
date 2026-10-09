# PDF và QA - Người 6, đã tích hợp với MMB Analysis

Bộ xuất giữ cấu trúc Vĩ mô → Ngành → Doanh nghiệp → Chiến lược → Rủi ro → Nguồn.
Renderer dùng ReportLab có sẵn trên máy thay cho WeasyPrint/GTK. Template HTML cũ
được giữ để tham khảo bố cục, không được thực thi trong luồng xuất PDF.

## Cài lại và dùng trên web

Chạy từ thư mục investment_hub:

```powershell
node scripts/install-pdf.mjs
npm start
```

Script tạo `packages/pdf.module.json`, cài phiên bản PDF mới và giữ nguyên các
module khác. Sau khi sửa nguồn, chạy lại script rồi refresh web. Nếu sửa runtime
hoặc server, khởi động lại server.

Tạo hoặc mở lần phân tích → nhận output → **Tạo PDF bằng module → Tải PDF**.
Pending vẫn xuất được, nhưng kết luận là Chưa đủ dữ liệu. Khi data/strategy đổi,
server vô hiệu PDF cũ theo revision.

## Runtime

Python 3.10+; `reportlab>=4,<5` để xuất PDF, `pypdf` để chạy QA.
Máy này đã có các thư viện trong runtime Codex; không cài dependency mới.
Máy khác đặt PYTHON_BIN tới môi trường nhóm và cài:

```powershell
python -m pip install -r "PDF Format/report/requirements.txt"
```

Ứng dụng ưu tiên PYTHON_BIN, tiếp đến runtime Python của Codex nếu tồn tại,
cuối cùng là python/python3 trong PATH. Không ghi đường dẫn người dùng cố định.

Font tiếng Việt dùng Arial trên Windows hoặc DejaVu Sans trên Linux, nhúng vào PDF.
Có thể đặt PDF_FONT_DIR tới thư mục chứa arial.ttf/arialbd.ttf hoặc
DejaVuSans.ttf/DejaVuSans-Bold.ttf. Thiếu font sẽ báo lỗi, không đổi sang font thiếu glyph.

## Hợp đồng adapter

run.py nhận một JSON trên stdin:

```text
{"analysis": <analysis.json do hệ thống assemble>, "output_dir": <đường dẫn tuyệt đối>}
```

Ghi report.pdf và report_manifest.json vào output_dir. Stdout đúng một JSON:

```text
{"pdf_filename":"report.pdf","manifest":{
  "schema_version":"1.0","run_id":<id>,"ticker":<ticker>,"as_of_date":<date>,
  "overall_status":<status>,"generated_at":<ISO8601 có múi giờ>,
  "sections_present":["macro","industry","company","strategy","risks","sources"],
  "warnings":<analysis.warnings>,"pdf_filename":"report.pdf"
}}
```

Log/lỗi vào stderr và exit khác 0 khi thất bại. Không tự thêm module thiếu hoặc
sửa run_id/ticker/ngày chốt. Adapter từ chối input pending chưa có định danh;
pending_analysis.json gốc chỉ dùng để xem layout bằng CLI.

## CLI và kiểm thử

```powershell
python -X utf8 "PDF Format/report/src/pdf_generator.py" <analysis.json> --output-dir <folder>
python -X utf8 "PDF Format/report/src/qa_checklist.py" <analysis.json> --output-dir <folder>
npm test
```

QA kiểm đúng cặp analysis/manifest/PDF trong output-dir, không tìm một PDF bất kỳ.
PASS chỉ xác nhận kiểm tra cấu trúc; WARN là chưa đủ dữ liệu; MANUAL cần kiểm tra
nguồn/chiến lược/tái lập/gói nộp. Font nhúng và text trích được chưa thay thế việc
render các trang để kiểm bảng tràn. Test Python và API dùng fixture phần mềm,
không phải dữ liệu nghiên cứu.

## Quy tắc nội dung

- Chỉ dùng display_conclusion và conclusion_usable, không trình bày khuyến nghị
  raw khi còn thiếu dữ liệu, cảnh báo hoặc lỗi.
- Escape mọi nội dung JSON thành văn bản; không chạy HTML hoặc truy cập URL.
- Bảng A4 lặp header, ngắt trang, xuống dòng ID/URL và có số trang.
- Giữ số thập phân, số 0 và đơn vị/tần suất; null là Chưa có. Tỷ lệ 0.12 được giữ
  nguyên với chú thích tương ứng 12%, không âm thầm đổi thang đo.
- Bảng giá hiển thị tối đa 10 phiên gần nhất; dashboard vẽ toàn kỳ phân tích;
  không nội suy, không tự điều chỉnh corporate actions. BCTC giữ kỳ/phạm vi.
- Giữ lý thuyết đầu tư, quy tắc, bằng chứng, công thức và nguồn với ngày công bố,
  ngày truy cập, locator và trạng thái xác minh.
- Không tạo quan sát, công thức đầu tư mới hoặc kết quả backtest.
