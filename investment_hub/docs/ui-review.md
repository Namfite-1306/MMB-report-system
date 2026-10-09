# Phân tích UI/UX và kiểm tra giao diện — 09/10/2026

## Ảnh tham chiếu

Ba ảnh `preview-1.avif`, `preview-2.avif`, `preview-3.avif` là các bố cục giới thiệu sản phẩm: nền gần đen, chữ trắng rất lớn, khoảng trống rộng, biểu tượng xanh và vật thể kính với ánh sáng xanh–cyan–tím. Ảnh 1 dẫn mắt bằng bậc thang chéo; ảnh 2 đặt chữ lớn trên khối nền; ảnh 3 chia chữ bên trái, vật thể kính bên phải. Các ảnh không thể hiện form, trạng thái dữ liệu hay luồng xử lý lỗi, nên cần thiết kế các phần đó theo mục đích thực tế của Investment Hub.

## Cách áp dụng

- Hero chia hai vùng: tên hệ thống và CTA bên trái; ba thẻ kính Dữ liệu / Chiến lược / Báo cáo trên bệ sáng bên phải. Đồ họa dựng bằng CSS, không cần thư viện hay ảnh tải từ ngoài.
- Bảng màu nền `#08090b`, chữ chính `#f5f6f7`, chữ phụ `#a1a7ae`, nút chính `#b7f86b`; cyan và tím giúp phân biệt module. Hiệu ứng tập trung ở hero để phần thao tác dễ đọc.
- Điều hướng cố định và ba bước có liên kết thật: thiết lập input → nhận dữ liệu và chiến lược → xem và xuất báo cáo.
- Desktop đặt form bên trái, workspace bên phải; màn hình hẹp chuyển thành một cột. Thẻ dữ liệu giữ tên người phụ trách, số chỉ số, số nguồn, phương thức nhận output và trạng thái.
- Tiến độ chỉ đếm output có trạng thái `ok`; output `pending`, `partial`, `error` không được tính hoàn chỉnh. Đây là tiến độ bàn giao, không chứng nhận chất lượng phân tích hay độ đúng của kết luận.
- Nút bị khóa có mô tả điều kiện. Phần cài module và nhật ký thu gọn; lỗi phân tích tự mở nhật ký. Thông báo có nút đóng, nội dung đọc được bởi trình đọc màn hình.
- Nút upload thật hỗ trợ bàn phím; CTA đưa focus vào mã cổ phiếu; có liên kết bỏ qua phần giới thiệu, viền focus và hỗ trợ giảm chuyển động.
- Khi mở lại lần đã lưu, form đồng bộ input của lần đó. Bảng chỉ số có tiêu đề cột và vùng cuộn ngang. Giá trị đầu vào vẫn được giữ nguyên.

## Phạm vi sửa

`public/index.html`, `public/style.css`, `public/app.js`. Không thêm dependency hoặc thay đổi API, hợp đồng dữ liệu, công thức hay dữ liệu nhóm. Các màu chính nằm trong biến CSS ở đầu `style.css`; nội dung và bố cục nằm trong `index.html`; thẻ module và trạng thái được dựng ở `app.js`.

## Kiểm tra đã thực hiện

1. Chụp giao diện trước khi sửa và đối chiếu ba ảnh tham chiếu.
2. Chụp hero và workspace desktop (viewport thực tế 1280 px), giao diện hẹp (428 px). Phát hiện tiêu đề bị cắt ở khung hẹp và sửa bằng cỡ chữ theo viewport; chụp lại xác nhận. Không có cuộn ngang toàn trang ở hai kích thước đã kiểm tra; các ô nhập ngày nằm trong form.
3. Kiểm tra CTA đặt focus vào ticker và điều hướng tới form.
4. Trong server kiểm thử riêng ở port 3111: tạo request ghi rõ KIỂM THỬ UI, không chứa quan sát hay kết luận đầu tư; tải request.json; nhận JSON pending hợp lệ; kiểm tra JSON sai cú pháp; đóng thông báo; tải lại trang và mở lần đã lưu; xác nhận ticker và ngày chốt được khôi phục.
5. Bấm Xem / In báo cáo, xác nhận tab báo cáo đúng lần phân tích và vẫn hiển thị chưa đủ dữ liệu. Không thực hiện in vật lý hay xuất PDF từ trình duyệt.
6. `node --check public/app.js` đạt. Bộ `npm test` hiện có đạt 15/15 sau khi chạy với quyền kết nối localhost; lần đầu trong sandbox bị chặn kết nối, không phải lỗi assertion nghiệp vụ. Không có console error trong luồng UI tạo input / upload / download đã kiểm tra.

Ảnh đối chiếu lưu ở `outputs/ui_review_20261009`. Các file và lần phân tích thử nằm trong `isolated-workspace` ở cùng thư mục, tách khỏi storage thật của Investment Hub. Server thử dừng sau khi kiểm tra.

## Giới hạn

Chưa kiểm tra trên thiết bị vật lý hoặc mọi kích thước màn hình. Chưa có gói module thật của nhóm trong workspace chạy UI, nên chưa xác nhận qua giao diện việc chạy các gói của thành viên hoặc tạo PDF bằng các gói đó. Các cơ chế execute/PDF hiện có được kiểm tra bởi bộ test API. Giao diện báo cáo in giữ định dạng hiện có để phù hợp bản in.
