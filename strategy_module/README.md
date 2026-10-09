# Module chiến lược đầu tư

Nhận dữ liệu macro, industry, company theo schema 1.0.

Đơn vị:
- Tiền và giá trị: VND, VND/share.
- Tỷ lệ: thập phân; 0.2 tương ứng 20%.
- Ngày: YYYY-MM-DD.
- Thiếu dữ liệu: null.

Kiểm tra:
python -m py_compile strategy.py
python strategy.py --self-test

Chạy:
python strategy.py input_example.json strategy.json

Đầu ra:
schema_version, run_id, ticker, as_of,
status, data, sources, warnings, errors.

Phạm vi v1:
- Biên an toàn từ khoảng định giá có giả định.
- Lợi suất giá điều chỉnh 6 tháng, chỉ mô tả quá khứ.
- Định giá tương đối, CAPM và tối ưu danh mục chưa triển khai.
- Không tự động khuyến nghị mua/bán.

Trạng thái kiểm chứng:
- input_example.json là mẫu không có dữ liệu thật.
- Chưa kiểm chứng dữ liệu thật.
- Trang sách Graham/Dodd còn cần bổ sung.
- Cần thống nhất tên trường với các module còn lại.