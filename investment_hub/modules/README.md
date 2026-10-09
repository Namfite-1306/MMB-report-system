# Nơi cài module

PDF người 6 đã cài bằng `scripts/install-pdf.mjs`. Module dữ liệu/chiến lược do các
thành viên bàn giao. Dùng giao diện để tải gói
`<module>.module.json` được đóng gói bằng `scripts/package-module.mjs`.

Máy chủ lưu từng phiên bản riêng vào `<module>/versions/<uuid>/`, và lưu phiên bản
đang dùng trong `registry.json`. Cài gói không tự chạy chương trình.
Mã nguồn được chạy với quyền tài khoản local, không phải trong sandbox.

Năm loại module: `macro`, `industry`, `company`, `strategy`, `pdf`.
Các thư viện Python hoặc Node mà thành viên dùng phải có trên máy chạy;
ứng dụng không tự cài dependency từ gói bàn giao.
