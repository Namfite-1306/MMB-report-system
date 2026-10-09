# Bàn giao module 3 - 09/10/2026

## Kết quả

Đã đọc Sheet 1 và hợp đồng V1. Python 3.10+, thư viện chuẩn. Đầu vào là request chung; giữ nguyên schema_version/run_id/ticker/as_of_date. Không phụ thuộc macro/industry để lấy dữ liệu.

HPG: snapshot thật có 437 phiên từ 2025-01-02 đến 2026-10-08, 50 tin trang đầu VCI, 2 BCTC hợp nhất issuer (FY2025 kiểm toán, H1/2026 soát xét). 66 dòng PDF đã đọc/đối chiếu; 64 dòng có phép so API/PDF khớp chính xác sau khi thống nhất dấu và kỳ. Hai EPS YTD không cộng quý để so.

Output YTD tính được 20/23 chỉ số, status=partial, errors=[] trong bản replay. P/E, P/B, vốn hóa null do thiếu bằng chứng giá spot/số cổ phiếu/cơ sở EPS có hiệu lực tại phiên. Đây là giới hạn thật của đầu vào, không phải công thức lấy sai hay mặc định giá trị 0.

| Số đối chiếu | H1/2026 |
|---|---:|
| Doanh thu thuần | 108.059.749.601.554 VND |
| LNST toàn tập đoàn | 15.480.392.467.117 VND |
| LNST cổ đông công ty mẹ | 15.365.022.248.705 VND |
| CFO | 12.641.697.117.285 VND |
| ROA 6 tháng, tài sản bình quân | 0,05767346 |
| ROE 6 tháng, vốn cổ đông mẹ bình quân | 0,11388359 |
| Doanh thu thuần YoY | 0,46955700 |
| LNST cổ đông mẹ YoY | 1,02150814 |

Không trình bày hai ROA/ROE này như tỷ lệ năm. Tăng trưởng doanh thu tính từ **doanh thu thuần**, khác mức tăng tính từ doanh thu trước giảm trừ trong thông cáo.

## Điểm cần báo cả nhóm

1. `industry.json` hiện tại có run_id khác request ví dụ doanh nghiệp. Người 5 phải tạo request chung và chạy lại module; không ghép khác run_id.
2. Module ngành hiện giữ nhiều số/nhận định cố định và cờ publication_date_verified=true. Trong checkout được đọc chưa có snapshot chứng minh mọi số. Cần người 2 đối chiếu lại; đây là thiếu bằng chứng quan sát được, **không phải kết luận rằng mọi số đều sai**.
3. Ngày issuer công bố FY2025 là 27/03/2026 và H1/2026 là 28/08/2026; publicDate của API muộn hơn. Không coi ngày cập nhật API là ngày công bố gốc.
4. API báo cáo quý có EPS có thể mang nghĩa lũy kế (HPG Q2/2026=1.781 trùng EPS H1). Không cộng EPS các quý. Dòng tiền/thu nhập tiền được đối chiếu theo tổng quý vào YTD; không suy rộng cấu trúc này cho nguồn khác khi chưa kiểm.
5. API raw giá dùng VND; wrapper vnstock thường đổi giá sang nghìn đồng. Adapter này đọc **raw**, không nhân 1.000 lần nữa.
6. BCTC 2026 phân loại lại một số tài sản/nợ đầu kỳ. Chỉ dùng đúng các tổng đã kiểm; không suy luận tăng trưởng các cấu phần khi cách phân loại khác.
7. Nguồn tin mới lấy trang đầu, chưa xác minh toàn bộ nội dung hoặc tác động; không lấy tiêu đề làm kết luận tích cực.
8. Phạm vi công thức phi tài chính; ngành ngân hàng/chứng khoán/bảo hiểm cần mapping và chỉ số chuyên biệt từ dữ liệu đã kiểm.

## Người 4/5/6 đọc gì

Người 4: `data.metrics[]` + frequency/kỳ/scope, findings/risks/evidence_refs, warnings/status. Người 5: `analyze_company(request, ...)`, `validate_company_output`; nạp envelope nguyên vẹn. Người 6: source_refs, URL, ngày công bố, locator và cách hiển thị null. T+135 đợi PDF thật để so số.

Bộ kiểm thử gồm công thức, thiếu dữ liệu, chia 0, scope, publication cutoff, TTM, SHA256, EPS/cơ sở cổ phiếu và replay dữ liệu thật. Xem `validation_summary.json` để biết số ca kiểm cuối cùng.
