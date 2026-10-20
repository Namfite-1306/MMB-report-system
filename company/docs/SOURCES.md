# Nguồn và cách kiểm

Khảo sát 09/10/2026; source URL trong từng response `.meta.json` là căn cứ cho snapshot thực tế.

| Nội dung | Nguồn |
|---|---|
| Giá raw VCI | https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart |
| BCTC / mapping VCI | https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/HPG/financial-statement ; thêm section BALANCE_SHEET/INCOME_STATEMENT/CASH_FLOW |
| Tên trường BCTC VCI | https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/HPG/financial-statement/metrics |
| Tin doanh nghiệp VCI | https://iq.vietcap.com.vn/api/iq-insight-service/v1/news ; query thực tế trong news.meta.json |
| Lịch công bố Hòa Phát | https://www.hoaphat.com.vn/quan-he-co-dong/bao-cao-tai-chinh |
| PDF FY2025 | https://file.hoaphat.com.vn/hoaphat-com-vn/2026/03/20260327-hpg-bctc-hop-nhat-nam-2025-sau-kiem-toan.pdf |
| PDF H1/2026 | https://file.hoaphat.com.vn/hoaphat-com-vn/2026/08/20260828-hpg-bctc-hop-nhat-soat-xet-6-thang-2026-va-giai-trinh-1-2.pdf |
| Repo nhóm đọc cấu trúc | https://github.com/Namfite-1306/MMB-report-system |
| Tài liệu triển khai endpoint VCI | https://github.com/thinh-vu/vnstock/tree/main/vnstock/explorer/vci |
| Kiểm raw giá / wrapper đổi đơn vị | https://github.com/thinh-vu/vnstock/blob/main/vnstock/core/utils/transform.py |
| Repo miner tham khảo trong đề | https://github.com/Tumiqa/vn-annual-report-miner |

Đã đọc source code adapter VCI để xác định endpoint/schema và cách wrapper đổi giá. Module viết riêng bằng urllib và không import/copy package vnstock; không dùng số tài chính có sẵn hoặc công thức miner để tạo output. Repo miner chỉ là lựa chọn để thu thập PDF sau này; chưa tích hợp miner trong bản này.

PDF scan: OCR dùng hỗ trợ tìm dòng, nhưng verified bundle được xác nhận từ ảnh trang gốc. Trang PDF annual 7–11 và interim 9–13 giữ locator; tên báo cáo/đơn vị/phạm vi/kỳ được kiểm trên cùng các trang. Ngày công bố đối chiếu từ lịch issuer, không suy từ đường dẫn hoặc ngày ký.

Số cố định trong build_hpg_verified.py là **bản chép snapshot có nguồn và ngày**, không cập nhật tự động, không được tái dùng cho ticker khác. Khi chọn ngày chốt/kỳ mới, collector vẫn lấy dữ liệu API mới nhưng số đã kiểm chỉ đủ cho các kỳ trên; output partial báo rõ nếu thiếu kỳ.
