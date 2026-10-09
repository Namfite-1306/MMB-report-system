# Tích hợp PDF người 6 - 09/10/2026

## Các vấn đề phát hiện và cách sửa

1. CLI cũ đọc đường dẫn JSON và in log stdout, không khớp giao thức stdin/stdout của người 5. Bổ sung run.py adapter nhận analysis/output_dir, chỉ trả JSON stdout; CLI độc lập vẫn được hỗ trợ.
2. Manifest cũ chỉ có bốn module và bỏ module error, dù template có thể render chúng. Manifest mới liệt kê đủ sáu phần macro/industry/company/strategy/risks/sources, kể cả phần đang chờ hoặc lỗi; giữ nguyên định danh snapshot.
3. Template cũ lấy kết luận raw của strategy, có thể trái với display_conclusion đã bị hệ thống chặn. Renderer mới chỉ lấy display_conclusion; trạng thái hoặc bằng chứng chưa đủ điều kiện giữ nhãn insufficient_data.
4. Môi trường máy này không có Jinja2/WeasyPrint. Dùng ReportLab 4.4.9 có sẵn, không cài GTK hoặc dependency mới. Font Arial tiếng Việt được nhúng. Giữ template HTML và output cũ của thành viên làm tham chiếu, không sử dụng trong pipeline mới.
5. Làm tròn BCTC/giá đến số nguyên có thể mất thông tin; HTML interpolation không autoescape có thể đưa markup input vào báo cáo. Renderer giữ giá trị raw, phân biệt null/0 và escape văn bản; URL chỉ là nội dung nguồn, không được truy cập.
6. Checklist cũ có thể PASS dữ liệu rỗng và kiểm PDF bất kỳ thay vì đúng lần phân tích. QA mới kiểm cặp analysis/manifest/PDF cụ thể, tách PASS cấu trúc / WARN thiếu dữ liệu / MANUAL nội dung cần review.
7. Python trong PATH của máy này là WindowsApps alias. Runner ưu tiên PYTHON_BIN, fallback runtime Codex theo home directory nếu tồn tại; không hardcode tên tài khoản. Đã khởi động lại server với runner mới.

## Vị trí mã nguồn và bàn giao

- PDF Format/report/src/pdf_generator.py: renderer.
- PDF Format/report/run.py: adapter.
- PDF Format/report/src/qa_checklist.py: kiểm tra cặp input/output.
- scripts/install-pdf.mjs: đóng gói/cài lại PDF, giữ module khác.
- lib/python-runtime.mjs và lib/plugins.mjs: lựa chọn Python.
- packages/pdf.module.json: gói module; registry chọn phiên bản đã cài trong modules/pdf/versions.
- tests/pdf.test.mjs và PDF Format/report/tests/test_pdf.py: test renderer và API PDF thật.

## Xác minh

- npm test: 17/17 test Node đạt, trong đó một test chạy ba test Python và một test chạy PDF thật qua API. Không skip trên máy này.
- Chặn kết luận raw; kiểm module thiếu/sai định danh không tự sửa; bảng dài 55 dòng, URL dài, literal markup và số thập phân; PDF tiếng Việt A4.
- API tạo/tải PDF thật, manifest đúng run_id và invalidate sau khi cập nhật ngành.
- Browser trên server thử riêng port 3111: tạo input ghi rõ kiểm thử, bấm Tạo PDF bằng module, nhận thông báo hoàn tất, Tải PDF tải được file, không có console error. Web chính port 3000 đã hiện Đã cài: PDF.
- Render bằng Poppler và kiểm ảnh hai trang PDF pending cùng các trang bảng dài. Dữ liệu thử tách khỏi storage thật, không chứa kết quả nghiên cứu đầu tư. Ảnh minh chứng nằm ở outputs/pdf_merge_20261009.

## Giới hạn

Chưa có snapshot đầy đủ của người 1-4 để đối chiếu số liệu đầu tư thực tế. QA không chứng nhận tính đúng của nguồn, lý thuyết hoặc hiệu quả chiến lược. Template cũ không được thực thi; sửa bố cục PDF hiện tại ở renderer ReportLab. Chuyển sang máy khác cần Python/ReportLab và cặp font được ghi trong README module.
