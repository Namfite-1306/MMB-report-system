# Lộ trình hoàn thiện MMB Analysis — 13/10/2026

Đề xuất dựa trên mã nguồn và luồng HPG đã kiểm tra. Đây là kế hoạch sản phẩm, không phải cam kết hệ thống đã có các tính năng dưới đây. Hệ thống hiện phục vụ chạy local; các việc cần nguồn dữ liệu, tài khoản hoặc hạ tầng sẽ chỉ kết nối/triển khai khi có cấu hình và phạm vi được thống nhất.

## Đã sửa trong lần rà soát này

- Danh sách lần phân tích xếp theo thời gian tạo thay vì thứ tự UUID. Thêm kỳ BCTC và phạm vi vào nhãn để phân biệt cùng mã/ngày chốt.
- Khóa form trong lúc chạy để không làm mất chỉnh sửa giữa chừng. Thu thập input trước khi khóa và giữ các giá trị gốc.
- Lưu nháp riêng từng lần trên trình duyệt, khôi phục khi reload/mở lại, có nút trở về cấu hình đã lưu. Nháp chưa áp dụng không được chạy như input chính thức.
- Xử lý mất kết nối/phản hồi không phải JSON, giữ mã HTTP cho trường hợp lần lưu không tồn tại. Thử kết nối lại chỉ đọc trạng thái, không tự gửi lại yêu cầu ghi.
- Tìm chỉ số không dấu, chọn nhóm dữ liệu, lọc giá trị thiếu, đếm kết quả và trạng thái không tìm thấy. Số 0 vẫn là dữ liệu có, không coi là thiếu.
- Loại hướng dẫn vuốt khỏi báo cáo HTML để in. Cập nhật README cho đúng tên nút.
- Báo cáo HTML hiển thị kỳ/phạm vi BCTC, số tháng và trạng thái/quy tắc bằng nhãn dễ đọc; PDF tự động vẫn dùng renderer riêng, cần đợt đồng nhất đầy đủ tiếp theo.

## Kiểm chứng đợt sửa

- 29/29 kiểm thử đạt, gồm thứ tự phiên mới/cũ, tìm không dấu, giữ số 0, lỗi kết nối và pipeline/PDF.
- Trên trình duyệt: bản nháp khôi phục sau reload và sau chuyển sang lần khác rồi quay lại; nút chạy khóa khi nháp chưa lưu. Bỏ nháp trả về input đã lưu.
- Workflow HPG chạy lại và tạo PDF; các ô ticker/số tháng khóa trong khi xử lý và mở lại khi hoàn tất.
- Chủ động dừng server để thử một yêu cầu đọc: hiện thông báo mất kết nối, giữ đúng phiên đang mở; khởi động lại và bấm thử kết nối phục hồi trạng thái/PDF, không chạy lại workflow.
- Tìm “doanh thu” trả hai trong 33 chỉ số; lọc thiếu trả ba chỉ số của bộ dữ liệu được kiểm tra. Từ khóa không khớp có thông báo riêng.
- Viewport 390×844: trang không tràn ngang; bảng 680px nằm trong vùng cuộn riêng. Đây là mô phỏng viewport, chưa phải thử trên thiết bị vật lý.
- Đối chiếu báo cáo HTML: có BCTC Năm/Hợp nhất và nhãn trạng thái dễ đọc; hướng dẫn vuốt không còn trong bản in. Không thay đổi giá trị đầu vào để làm tăng số trụ cột đủ điều kiện.

## Thứ tự đề xuất

| Ưu tiên | Hạng mục tôi có thể triển khai | Giá trị đối với người dùng | Đầu vào/điều kiện cần | Tiêu chí hoàn thành |
|---|---|---|---|---|
| 1 | Trung tâm chất lượng dữ liệu | Biết từng trụ cột thiếu trường gì, ngày nào và cần nguồn nào | Hợp đồng metric/rule của nhóm; bảng ánh xạ yêu cầu theo quy tắc | Mỗi trụ cột thiếu có danh sách đầu vào và đường tới nguồn/chỉ số; không dùng % chất lượng tùy ý |
| 1 | Quy trình cập nhật có kiểm chứng | Hạn chế dùng snapshot cũ với ngày chốt mới | Nguồn được phép dùng, cách cập nhật, khóa truy cập nếu cần | Có thời điểm dữ liệu/công bố/nhập, log lần cập nhật, phát hiện thay đổi đơn vị/phạm vi; giữ snapshot cũ để tái lập |
| 1 | Đồng nhất web và PDF | Báo cáo đọc như cùng một sản phẩm | Mẫu báo cáo và quy tắc định dạng thống nhất | Cùng nhãn, tỷ lệ, đơn vị, kỳ BCTC, cơ sở điều chỉnh giá, cảnh báo và nguồn; chữ tiếng Việt đúng, bảng không bị cắt |
| 2 | Trang phân tích cho nhà đầu tư | Giảm số bước phải hiểu công cụ bàn giao của nhóm | Xác định nhóm người dùng chính và mã được hỗ trợ | Tóm tắt doanh nghiệp → kết quả → bằng chứng → rủi ro; bộ thiết lập cơ bản/nâng cao; chế độ quản trị module riêng |
| 2 | Tra cứu cổ phiếu và thư viện phân tích | Tìm lại kết quả nhanh khi số phiên tăng | Danh mục ticker/sàn/ngành có nguồn | Tìm theo mã/ngày/kỳ, mở kết quả rõ trạng thái, có đường dẫn tới từng lần; không tự ghép cổ phiếu sai sàn |
| 2 | So sánh doanh nghiệp cùng ngành | Đọc vị trí tương đối thay vì một mã đơn lẻ | Peer và từng giá trị có nguồn, cùng ngày/kỳ/phạm vi | So sánh P/E, P/B, ROE, tăng trưởng với ghi chú chênh lệch kỳ; thiếu dữ liệu không thành 0 |
| 2 | Phân tích định giá và kịch bản | Hiểu kết luận phụ thuộc giả định nào | Quy tắc chiến lược, giả định DCF và chứng cứ được duyệt | Kịch bản cơ sở/tích cực/thận trọng, bảng nhạy cảm, ghi nguồn từng giả định; kết quả tái tính được |
| 2 | Benchmark và rủi ro | Biết hiệu quả so với thị trường và phạm vi bất định | Giá điều chỉnh/total return, benchmark, chu kỳ dữ liệu phù hợp | Lợi suất, drawdown, biến động tính đúng trên cùng lịch; phân biệt thay đổi giá với tổng lợi suất |
| 3 | Trải nghiệm khi tác vụ dài | Biết phần nào đang chạy và xử lý lỗi cục bộ | Thiết kế trạng thái tác vụ trên server | Tiến trình từng bước thực tế, lưu kết quả khi đóng tab, chạy lại đúng phần lỗi; không hiển thị phần trăm giả |
| 3 | Chia sẻ và cộng tác | Nhóm cùng xem một kết quả đã đóng băng | Mô hình quyền, người dùng, nơi triển khai và dữ liệu được phép chia sẻ | Đăng nhập, phân quyền, phiên bản báo cáo, nhật ký thay đổi; chỉ chia sẻ đúng snapshot được chọn |
| 3 | Vận hành production | Dùng ổn định ngoài máy local | Hosting/domain, cơ chế chạy module và ngân sách | Tách quyền chạy mã module khỏi web, quản lý secrets, queue, database, backup/khôi phục, logging, giới hạn tài nguyên, CI và kiểm tra bảo mật trước phát hành |

## Gói tiếp theo nên chọn

**Để demo/báo cáo nhóm:** làm trung tâm chất lượng dữ liệu, đồng nhất PDF và đơn giản hóa trang phân tích. Có thể triển khai trên các snapshot đã có, rồi đo ba thao tác: hiểu kết luận, tìm bằng chứng, tải báo cáo.

**Để hỗ trợ nghiên cứu đầu tư:** ưu tiên cập nhật nguồn, peer có bằng chứng từng giá trị, dữ liệu điều chỉnh và giả định chiến lược. Các đồ thị định giá chỉ nên bổ sung sau khi đáp ứng đầu vào.

**Để mở cho nhiều người dùng:** cần một đợt riêng về kiến trúc và quyền truy cập. Server local hiện cho chạy module do nhóm tin cậy bằng quyền tài khoản trên máy; không đưa nguyên kiến trúc này lên hosting công khai.

## Cách nghiệm thu

- Dùng các ca đủ/thiếu dữ liệu, ngày chốt lịch sử và thay đổi kỳ/phạm vi. Không chỉ nghiệm thu bằng HPG một cấu hình.
- Đối chiếu số hiển thị với JSON và PDF, kiểm tra số 0, null, giá trị âm, làm tròn và đơn vị.
- Thử bằng bàn phím và màn hình nhỏ, kiểm tra thông báo lỗi, nội dung dài và nguồn có nhiều liên kết.
- Cho người chưa biết app thực hiện một nhiệm vụ; ghi thời gian, thao tác bị kẹt và cách họ hiểu kết luận. Chưa có số liệu thử nghiệm người dùng thật trong đợt này.
- Chốt một nhóm ưu tiên trước khi mở rộng. Không thể cam kết thời gian cho kết nối dữ liệu/hosting khi chưa biết nguồn, quyền truy cập và hạ tầng.
