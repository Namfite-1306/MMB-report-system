# MMB Analysis

Hệ thống phân tích đầu tư của nhóm: Vĩ mô → Ngành → Doanh nghiệp → Chiến lược → Báo cáo PDF.
Ứng dụng chính nằm trong [`investment_hub/`](investment_hub/README.md). Node.js 20+
phục vụ giao diện HTML/CSS/JavaScript thuần; Python 3.10+ thực thi module và xuất PDF.

## Chạy từ repo đã clone

```powershell
cd investment_hub
python -m pip install -r "PDF Format/report/requirements.txt"
node scripts/install-team.mjs
node scripts/install-pdf.mjs
npm start
```

Mở http://127.0.0.1:3000. Không cần `npm install`. Nếu máy có nhiều môi trường Python,
đặt `PYTHON_BIN` tới python.exe của môi trường đã cài ReportLab trước các lệnh Node.
Font tiếng Việt dùng Arial trên Windows hoặc DejaVu Sans trên Linux; xem README bộ PDF.

## Mã nguồn

- `macro-module/`: phần vĩ mô của người 1.
- `industry/`: phần ngành của người 2.
- `strategy_module/`: phần chiến lược của người 4.
- `investment_hub/MMB_company_module_nguoi3/`: doanh nghiệp, kiểm nguồn và snapshot HPG của người 3.
- `investment_hub/server.mjs`, `lib/`, `public/`: API, điều phối và giao diện người 5.
- `investment_hub/PDF Format/report/`: bộ PDF người 6 đã tích hợp.
- `investment_hub/integrations/`, `packages/`: adapter, bản nguồn tích hợp và gói cài module.

Dashboard có giá đóng cửa/MA20, khối lượng, doanh thu/lợi nhuận/dòng tiền và bộ lọc thời gian.
Biểu đồ được xuất trong HTML và PDF. Dữ liệu HPG được giữ để tái lập offline, gồm hai
PDF doanh nghiệp công khai và metadata/hash. Storage, báo cáo sinh ra, môi trường Python
và phiên bản module cài trên từng máy không được commit.

## Kiểm thử và giới hạn

```powershell
cd investment_hub
npm test
```

Các kiểm thử bao gồm hợp đồng, upload, bảo toàn output, dashboard, pipeline HPG và PDF.
Module dữ liệu chạy song song trước khi chiến lược đọc snapshot; PDF gắn với revision.
Kết luận bị chặn khi thiếu bằng chứng. Chuỗi giá chưa xác minh đầy đủ điều chỉnh corporate
actions; chưa có backtest hay kết quả hiệu quả đầu tư. Xem
[`workflow và giới hạn dữ liệu`](investment_hub/docs/team-workflow.md).

Ứng dụng lắng nghe localhost, chưa thiết kế để triển khai công khai nhiều người dùng.
