# Đánh giá UX MMB Analysis — 12/10/2026

## Nhận định từ góc nhìn nhà đầu tư

Giao diện có bản sắc, bố cục nhất quán và hỗ trợ sáng/tối. Trước lần sửa này, luồng thao tác thiên về nhận output của nhóm: người dùng phải hiểu module, JSON và mã chỉ số trước khi biết dữ liệu có đủ để sử dụng kết luận hay không. Với nhà đầu tư, ba câu hỏi cần trả lời trước là: dữ liệu bao phủ thời gian nào, cơ sở của kết luận nằm ở đâu, và thiếu gì để tiếp tục.

Bản sửa đưa phạm vi dữ liệu và điều kiện sử dụng kết luận lên đầu, giảm thông tin kỹ thuật trên đường thao tác chính, đồng thời giữ dữ liệu gốc để kiểm tra. App phù hợp hơn để đọc, đối chiếu và xuất báo cáo. Việc cải thiện UX không bổ sung bằng chứng còn thiếu hoặc nâng mức đủ điều kiện của chiến lược.

## Các vấn đề và cách xử lý

| Mức ưu tiên | Vấn đề trước sửa | Tác động đối với nhà đầu tư | Thay đổi đã thực hiện |
|---|---|---|---|
| Cao | “Chưa đủ dữ liệu” không chỉ rõ thiếu gì | Không biết nên sửa input hay bổ sung nguồn | Thẻ phạm vi giá/BCTC và danh sách phần còn thiếu; phân biệt đang chờ, lỗi module, thiếu BCTC, thiếu đầu vào chiến lược |
| Cao | Kỳ yêu cầu dễ bị hiểu là kỳ dữ liệu thực có | Có thể đọc biểu đồ với kỳ vọng sai về độ dài lịch sử | Hiển thị ngày đầu/cuối thực có, số phiên, kỳ yêu cầu; nhắc khi ngày bắt đầu dữ liệu trễ hơn yêu cầu trên 7 ngày lịch |
| Cao | Thay cấu hình nhưng kết quả vẫn thuộc lần cũ | Có thể chạy/xuất báo cáo với cách hiểu sai về input | Cảnh báo cấu hình chưa lưu; khóa chạy workflow, module riêng và tạo lại PDF cho đến khi tạo lần phân tích mới |
| Cao | Tỷ lệ thập phân và mã chỉ số khó đọc | Dễ hiểu nhầm 0,0709 thành 0,0709% | Nhãn dễ đọc, tỷ lệ thành %, số tiền lớn thành tỷ VND; có đơn vị, kỳ, nguồn và giá trị gốc để đối chiếu |
| Trung bình | Nút tải báo cáo nằm sau nhiều bảng | Phải cuộn dài để lấy kết quả | Tải PDF ở đầu lần phân tích và đầu phần báo cáo; trạng thái sẵn sàng tải rõ ràng |
| Trung bình | Thông báo nổi che tiêu đề và ít thông tin tiến trình | Gây cản trở đọc, dễ tưởng app bị treo | Thông báo nằm trong luồng trang; lỗi dùng alert và đưa vào vùng nhìn; hiển thị bước xử lý thay vì phần trăm giả |
| Trung bình | Reload phải mở lại kết quả | Mất mạch đọc | Khôi phục lần phân tích gần nhất; cấu hình snapshot HPG có nút điền nhanh và ngày bàn giao rõ ràng |
| Trung bình | Biểu đồ thu nhỏ trên điện thoại | Khó đọc nhãn và số | Biểu đồ cuộn trong khung, giữ kích thước tối thiểu; nút lọc cao tối thiểu 44px, khung hỗ trợ bàn phím và có hướng dẫn vuốt |
| Trung bình | Chỉ có đường biểu đồ, thiếu số liệu để đối chiếu | Khó kiểm tra một phiên cụ thể | Bảng mở rộng 20 phiên cuối trong khoảng đang chọn: giá, MA20, khối lượng |
| Thấp | Công cụ của nhóm lấn át đường đọc báo cáo | Tăng tải nhận thức | Đưa thao tác chạy riêng/nhận JSON vào phần mở rộng; giữ một nút chính “Phân tích & tạo báo cáo” |

Ngưỡng 7 ngày là quy tắc nhắc UX để tránh coi ngày nghỉ giao dịch thông thường là thiếu lịch sử; không phải kiểm định đầy đủ về chuỗi giá. Bảng phiên cuối là phần xem nhanh, không thay thế toàn bộ chuỗi dữ liệu trong analysis.json.

## Phạm vi kiểm tra thực tế

- Đi qua luồng chọn input, tạo lần phân tích, chạy workflow, tạo PDF, đọc nguồn và mở lại lần lưu bằng trình duyệt tại localhost.
- HPG, ngày chốt 31/12/2025, yêu cầu giá từ 01/01/2023, BCTC Quý hợp nhất: workflow và PDF chạy được; giá thực có 362 phiên từ 24/07/2024 đến 31/12/2025. Không có BCTC Quý phù hợp đã xác minh tại ngày chốt; hệ thống giữ trạng thái thiếu dữ liệu.
- HPG, snapshot ngày chốt 09/10/2026: lựa chọn Quý thiếu BCTC. Nút gợi ý tạo một lần phân tích mới với BCTC Năm chỉ xuất hiện khi có dữ liệu năm cùng phạm vi và nguồn công bố phù hợp. Không tự đổi input hoặc kết quả của lần cũ.
- HPG, BCTC Năm hợp nhất, kỳ giá 01/01/2025–08/10/2026: có 437 phiên giá và hai kỳ BCTC năm 2024/2025 phù hợp. Chiến lược vẫn thiếu đầu vào ở 8/9 trụ cột, không đủ điều kiện sử dụng kết luận.
- Bộ lọc một tháng: 23 phiên từ 08/09/2026 đến 08/10/2026; thay đổi giá -7,78%. Đây là thay đổi giá, chưa bao gồm cổ tức và phí giao dịch.
- Đối chiếu GDP: giá trị gốc 0,0709 được trình bày thành 7,09%, giữ nguồn và ngày công bố để kiểm tra.
- Kiểm tra bố cục ở viewport 390×844 và desktop; trang không tràn ngang tại kích thước đã kiểm tra, biểu đồ và bảng có vùng cuộn riêng. Đây là mô phỏng viewport, chưa phải thử trên điện thoại vật lý.
- Bộ kiểm thử 24 trường hợp bao gồm adapter, các kỳ/phạm vi BCTC thiếu dữ liệu, dashboard, định dạng, điều kiện gợi ý dữ liệu năm và pipeline/PDF. Không thay đổi thuật toán đầu tư trong lần sửa UX này.

Ảnh đối chiếu được lưu ngoài mã nguồn tại `outputs/ux_review_20261012` của workspace: before-setup, before-report, after-coverage, after-report và after-dashboard-mobile. Dữ liệu phân tích sinh ra vẫn nằm trong storage bị Git ignore.

## Những giới hạn còn lại và thứ tự cải thiện

1. **Bổ sung dữ liệu cho chiến lược:** ưu tiên các trường đang thiếu của 8 trụ cột và bằng chứng cho quy tắc. Chưa thể coi một PDF xuất thành công là chiến lược đủ căn cứ.
2. **Xác minh chuỗi giá:** cần làm rõ giá điều chỉnh, sự kiện chia tách/cổ tức và phạm vi thiếu phiên trước khi dùng để tính hiệu quả đầu tư. Hiện app ghi rõ cách điều chỉnh của nhà cung cấp chưa được xác minh.
3. **Cập nhật và phủ thêm doanh nghiệp:** snapshot HPG không phải nguồn realtime. Chưa xác nhận độ phủ và chất lượng workflow với nhiều mã trong lần UX audit này. Nên công bố danh sách mã hỗ trợ và ngày cập nhật từng bộ dữ liệu.
4. **Giảm bước thiết lập cho người mới:** có thể tách bộ lọc cơ bản và nâng cao, tự tra cứu tên ngành từ nguồn xác minh. Hiện tên ngành, kỳ BCTC và phạm vi vẫn yêu cầu người dùng hiểu khái niệm.
5. **Thử nghiệm với người dùng thật:** cho một người chưa biết hệ thống làm ba việc: mở HPG, giải thích vì sao kết luận chưa sử dụng được, và tải báo cáo. Ghi tỷ lệ hoàn thành và chỗ họ phải hỏi. Chưa có số liệu usability, kiểm tra screen reader đầy đủ hoặc benchmark hiệu năng trong lần này.

Ưu tiên tiếp theo là chất lượng đầu vào chiến lược và minh bạch dữ liệu. Thêm đồ thị hoặc hiệu ứng trước khi giải quyết hai phần này sẽ không làm kết luận đáng tin cậy hơn.
