# Workflow nhóm đã tích hợp

Mở http://127.0.0.1:3000, tạo input rồi bấm **Chạy workflow & tạo PDF**.
Người 1/2/3 chạy song song; người 4 đọc đúng snapshot đầu ra đã lưu; người 6 xuất PDF.
PDF gắn với revision, cập nhật dữ liệu sẽ hủy hiệu lực PDF và chiến lược cũ.

## Chạy nhanh HPG đã bàn giao

- Ticker HPG, sàn HOSE; bỏ ô nhập mã ngành, tự tra tên ngành nếu để trống.
- Ngày chốt 2026-10-09; kỳ 2025-01-01 đến 2026-10-08.
- Chọn kỳ BCTC Năm, phạm vi Hợp nhất; nhập thời hạn và số tháng nhóm cần.
- Đây là cấu hình để tái lập dữ liệu bàn giao, không phải khuyến nghị đầu tư.
- Người 3 đọc snapshot HPG offline, kiểm SHA256 cả API và hai PDF gốc.
- Các mã khác gọi collector Vietcap (timeout từng yêu cầu 15 giây); chưa kiểm chứng đường chạy mạng trong lượt tích hợp. BCTC chưa đối chiếu giữ trong financial_candidates, không nâng thành số đã xác minh.

## Hợp đồng nối dữ liệu

`request.json`: schema 1.0, một run_id, ticker/sàn/ngành, ngày chốt, kỳ, thời hạn,
investment_horizon_months (số nguyên), financial_basis và statement_scope.
Mã ngành chỉ còn trong hợp đồng nội bộ để tương thích module người 2/3; lấy từ bảng
ánh xạ ticker người 2, mã chưa biết dùng nhãn UNCLASSIFIED, không đoán ngành.
Adapter thêm trường input cũ mà module vĩ mô cần; không thay run_id/ticker/ngày chốt.

Mỗi output có module/status/data/sources/warnings/errors/generated_at.
Source và metric ID chuyển sang prefix `macro:`, `industry:`, `company:`, `strategy:`;
tham chiếu đổi theo cùng bảng id_map. `native_output` giữ bản gốc trước chuyển đổi.
Các dòng có kỳ sau ngày chốt không vào bảng sử dụng; bản gốc vẫn được giữ để đối chiếu.
Các giá trị thiếu giữ null, không thay bằng 0.

Người 4 dùng strategy_v2 và strategy_rules_v2 thực tế, giữ 9 trụ cột và 6 tài liệu lý thuyết.
Các fact BCTC chỉ lấy từ dòng verified, cùng phạm vi, nguồn có ngày công bố đủ điều kiện.
Chỉ nối hai kỳ annual liên tiếp có cùng khoảng tháng/ngày; YTD/quý/TTM chưa đủ bằng chứng
để chuyển thành annual sẽ để trụ cột tài chính thiếu dữ liệu.
CAPEX cash âm được đổi dấu thành khoản chi dương cho công thức CFO - CAPEX của người 4;
giá trị gốc trong BCTC người 3 giữ nguyên. Các định nghĩa ROE/ROA trong strategy_v2
khác công thức vốn cổ đông mẹ của người 3; không coi hai chỉ số là tương đương.
Không tự dựng EBIT, nợ vay, kỳ trước, DCF, beta, premium, benchmark hay tin tức thiếu.
Rule evidence_refs trỏ nguồn canonical; native_evidence_refs giữ đường dẫn fact gốc.

## Giới hạn còn lại trong dữ liệu bàn giao

1. Vĩ mô là snapshot được xác minh đến 2025-01-06, không tự cập nhật. Ngày truy cập chỉ có ngày được chuyển thành timestamp lúc 00:00 +07:00 kèm retrieved_at_precision=date_only_in_handoff; không tuyên bố biết giờ tải thật.
2. Ngành chứa bảng peer tĩnh, thiếu source_refs cho từng giá trị. Không đưa chúng vào fact định giá của người 4. Peer có ngày định giá sau cutoff bị loại khỏi bảng sử dụng; mã chưa ánh xạ không dùng fallback khác ngành. Chưa kiểm chứng lại nội dung website nguồn trong lượt tích hợp.
3. Chuỗi giá HPG có cơ sở điều chỉnh nhà cung cấp chưa xác minh. Không nâng cờ adjusted=true để chạy momentum/risk/CAPM. Chưa có benchmark total return và giả định DCF.
4. Module chiến lược còn các giới hạn lý thuyết/nguồn do người 4 nêu. Trạng thái partial và kết luận insufficient_data là kết quả có chủ ý khi chưa đủ bằng chứng; PDF vẫn xuất đủ dữ liệu/cảnh báo.
5. Chưa có backtest, chi phí giao dịch/slippage hay hiệu quả ngoài mẫu. Không suy ra lợi nhuận tương lai từ số liệu bàn giao.

## Bảo trì và cập nhật phần nhóm

Mã gốc người 1/2/4 được copy vào integrations/vendor, thư mục clone trên E: giữ nguyên.
Module người 3 gốc và raw PDF giữ nguyên. Adapter nằm ở integrations/run.py.

```powershell
node scripts/install-team.mjs "E:/OneDrive/Documents/GitHub/Clone/MMB-report-system"
node scripts/install-pdf.mjs
npm start
```

PDF evidence của người 3 lớn hơn giới hạn gói text 8 MB, nên installer cục bộ copy hai PDF
và trang issuer vào phiên bản module, sau đó người 3 kiểm hash. **Không cài lại riêng
company.module.json bằng nút upload** vì gói text không chứa PDF binary. Giữ folder người 3
khi chuyển máy và chạy lại install-team. Các package khác có thể cài bằng giao diện.

Đã tham khảo README và cấu trúc của vn-annual-report-miner: đầu ra text mining/panel/BCTC
cần đối chiếu item, đơn vị, kỳ, scope và ngày công bố trước khi đưa vào verified bundle.
Không tự nhập chỉ số miner thành số đã xác minh; không cài thêm stack miner vào workflow
hiện tại. Có thể dùng đầu ra miner để bổ sung bundle theo hướng dẫn người 3.

## Xác minh

Dashboard dùng dữ liệu thật: đường giá/MA20 và cột khối lượng theo phiên; các mốc
không có quan sát không được lấp. MA20 là trung bình 20 dòng giá tới phiên đang tính,
thiếu bất kỳ giá nào trong cửa sổ thì MA20=null. Lọc 1/3/6 tháng/1 năm tính ngược từ
phiên cuối có trong dữ liệu; MA20 vẫn dùng các phiên trước cửa sổ hiển thị trong input.
Thay đổi giá=(giá cuối/giá đầu−1), chưa có cổ tức/chi phí. Đơn vị giá VND/share,
khối lượng shares (biểu đồ triệu shares); không nâng cơ sở điều chỉnh thành đã kiểm.
Biểu đồ tài chính chỉ dùng verified=true, đúng frequency/scope, đơn vị VND và nguồn
có ngày công bố đủ điều kiện. Hiển thị tỷ VND, giữ CFO âm/giá trị 0, thiếu giữ null.
Dashboard không thay logic/gating chiến lược. HTML/PDF xuất biểu đồ toàn kỳ;
bộ lọc tương tác trên web chỉ đổi phạm vi hiển thị.

`npm test`: contract, bảo toàn output cũ khi lỗi, chống path traversal, UTF-8,
PDF tiếng Việt, workflow thật HPG qua cả bốn module + PDF, cutoff lịch sử.
Giao diện được kiểm bằng trình duyệt: tạo HPG, chạy workflow, tải PDF, sáng/tối,
lưu lựa chọn theme và bố cục ở kích thước màn hình thực tế.
