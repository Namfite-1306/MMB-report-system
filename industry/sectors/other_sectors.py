"""Sector data profiles: Bán lẻ (5370), Bất động sản (8630), Chứng khoán (8770)."""
from industry.sectors.base import (
    PeerCompany,
    SectorFinding,
    SectorMetric,
    SectorProfile,
    SectorRisk,
    SectorSource,
)


def get_retail_sector(as_of_date: str = "2026-10-09") -> SectorProfile:
    sources = [
        SectorSource(
            source_id="ind_src_gso_retail_sales_2026",
            title="Tổng cục Thống kê (GSO) - Báo cáo Tổng mức bán lẻ hàng hóa và doanh thu dịch vụ tiêu dùng 9 tháng năm 2026",
            url="https://www.gso.gov.vn/du-lieu-va-so-lieu-thong-ke/2026/09/tong-muc-ban-le-hang-hoa-9-thang-nam-2026/",
            published_at="2026-09-29",
            retrieved_at="2026-10-09T08:00:00+07:00",
            locator="Chỉ tiêu tổng mức bán lẻ tăng 8.8% YoY",
            publication_date_verified=True,
        ),
        SectorSource(
            source_id="ind_src_vietstock_retail_benchmark",
            title="Vietstock Finance - Báo cáo Định giá & Chỉ số tài chính ngành Bán lẻ 2026",
            url="https://finance.vietstock.vn/nganh-nghe/5370/ban-le.htm",
            published_at="2026-09-30",
            retrieved_at="2026-10-09T08:15:00+07:00",
            locator="Bảng P/E, P/B và ROE ngành Bán lẻ",
            publication_date_verified=True,
        ),
    ]
    peers = [
        PeerCompany(
            ticker="FRT",
            name="CTCP Bán lẻ Kỹ thuật số FPT",
            exchange="HOSE",
            market_cap=24500000000000.0,
            comparison_basis="Mô hình tăng trưởng đột phá với chuỗi nhà thuốc Long Châu dẫn đầu toàn quốc và FPT Shop tái cơ cấu.",
            metrics={"pe": 32.5, "pb": 7.2, "roe": 0.225, "roa": 0.045, "net_margin": 0.018, "gross_margin": 0.215, "debt_to_equity": 2.85, "revenue_growth_yoy": 0.285},
        ),
        PeerCompany(
            ticker="DGW",
            name="CTCP Thế Giới Số",
            exchange="HOSE",
            market_cap=9800000000000.0,
            comparison_basis="Nhà phân phối ủy quyền ICT, thiết bị văn phòng và hàng tiêu dùng nhanh (FMCG) cho các thương hiệu hàng đầu thế giới.",
            metrics={"pe": 16.2, "pb": 2.85, "roe": 0.175, "roa": 0.068, "net_margin": 0.024, "gross_margin": 0.082, "debt_to_equity": 0.95, "revenue_growth_yoy": 0.165},
        ),
        PeerCompany(
            ticker="PNJ",
            name="CTCP Vàng bạc Đá quý Phú Nhuận",
            exchange="HOSE",
            market_cap=32000000000000.0,
            comparison_basis="Bán lẻ trang sức và quà tặng cao cấp chiếm lĩnh thị phần áp đảo với biên lợi nhuận ròng vượt trội ngành tiêu dùng.",
            metrics={"pe": 15.8, "pb": 3.12, "roe": 0.235, "roa": 0.145, "net_margin": 0.055, "gross_margin": 0.185, "debt_to_equity": 0.25, "revenue_growth_yoy": 0.142},
        ),
    ]
    metrics = [
        SectorMetric("ind_pe_median", "P/E trung vị ngành Bán lẻ", 16.0, "x", "annual", "2025-01-01", "2025-12-31", ["ind_src_vietstock_retail_benchmark"], "median_peer_pe"),
        SectorMetric("ind_pb_median", "P/B trung vị ngành Bán lẻ", 3.0, "x", "annual", "2025-01-01", "2025-12-31", ["ind_src_vietstock_retail_benchmark"], "median_peer_pb"),
        SectorMetric("ind_roe_avg", "ROE bình quân ngành Bán lẻ", 0.2117, "ratio", "annual", "2025-01-01", "2025-12-31", ["ind_src_vietstock_retail_benchmark"], "mean_peer_roe"),
        SectorMetric("ind_retail_sales_growth", "Tăng trưởng tổng mức bán lẻ tiêu dùng 9T/2026", 0.088, "ratio", "quarterly", "2026-01-01", "2026-09-30", ["ind_src_gso_retail_sales_2026"], "gso_retail_growth_yoy"),
    ]
    findings = [
        SectorFinding("ind_f01_retail_consumption_rebound", "Sức mua của người tiêu dùng nội địa đang phục hồi rõ nét sau các biện pháp giảm thuế VAT 2% và tăng lương cơ sở, giúp doanh thu bán lẻ toàn ngành cải thiện tốc độ tăng trưởng.", ["ind_src_gso_retail_sales_2026", "ind_retail_sales_growth"]),
        SectorFinding("ind_f02_retail_consolidation", "Xu hướng tinh gọn mạng lưới cửa hàng không hiệu quả, tối ưu hóa chuỗi cung ứng và mở rộng mô hình bán lẻ đa kênh (Omni-channel) giúp các chuỗi lớn mở rộng biên lợi nhuận hoạt động.", ["ind_src_vietstock_retail_benchmark"]),
    ]
    risks = [
        SectorRisk("ind_r01_consumer_sentiment_risk", "Rủi ro tâm lý người tiêu dùng thắt chặt chi tiêu các sản phẩm công nghệ không thiết yếu (ICT/CE) nếu áp lực chi phí sinh hoạt gia tăng.", ["ind_src_gso_retail_sales_2026"]),
    ]
    return SectorProfile("5370", "Bán lẻ tổng hợp & Chuyên doanh", "recovery", peers, metrics, findings, risks, sources)


def get_real_estate_sector(as_of_date: str = "2026-10-09") -> SectorProfile:
    sources = [
        SectorSource(
            source_id="ind_src_vars_real_estate_2026",
            title="Hội Môi giới Bất động sản Việt Nam (VARS) - Báo cáo Thị trường Bất động sản Việt Nam Quý 3/2026",
            url="https://vars.com.vn/bao-cao-thi-truong-bat-dong-san-viet-nam/",
            published_at="2026-09-25",
            retrieved_at="2026-10-09T08:00:00+07:00",
            locator="Mục 3: Tỷ lệ hấp thụ nguồn cung căn hộ và đất nền khu vực phía Nam & phía Bắc",
            publication_date_verified=True,
        ),
        SectorSource(
            source_id="ind_src_vietstock_bds_benchmark",
            title="Vietstock Finance - Báo cáo Định giá & Cơ cấu nợ vay ngành Bất động sản dân cư 2026",
            url="https://finance.vietstock.vn/nganh-nghe/8630/bat-dong-san.htm",
            published_at="2026-09-30",
            retrieved_at="2026-10-09T08:15:00+07:00",
            locator="Bảng P/B, P/E và D/E ngành Bất động sản",
            publication_date_verified=True,
        ),
    ]
    peers = [
        PeerCompany("KDH", "CTCP Đầu tư và Kinh doanh Nhà Khang Điền", "HOSE", 31500000000000.0, "Doanh nghiệp sở hữu quỹ đất sạch pháp lý hoàn chỉnh tại TP.HCM, cơ cấu tài chính lành mạnh, hợp tác cùng Keppel Land.", {"pe": 24.5, "pb": 1.75, "roe": 0.075, "roa": 0.042, "net_margin": 0.285, "gross_margin": 0.485, "debt_to_equity": 0.42, "revenue_growth_yoy": 0.325}),
        PeerCompany("NLG", "CTCP Đầu tư Nam Long", "HOSE", 18200000000000.0, "Dẫn đầu phân khúc nhà ở vừa túi tiền (Affordable housing) với chuỗi dự án Akari City, Mizuki Park, Waterpoint liên doanh đối tác Nhật Bản.", {"pe": 22.8, "pb": 1.35, "roe": 0.068, "roa": 0.038, "net_margin": 0.165, "gross_margin": 0.385, "debt_to_equity": 0.48, "revenue_growth_yoy": 0.185}),
        PeerCompany("DXG", "CTCP Tập đoàn Đất Xanh", "HOSE", 12400000000000.0, "Tập đoàn phát triển bất động sản và dịch vụ môi giới chiếm thị phần môi giới bán hàng lớn nhất miền Nam.", {"pe": 35.2, "pb": 1.15, "roe": 0.035, "roa": 0.015, "net_margin": 0.045, "gross_margin": 0.425, "debt_to_equity": 0.65, "revenue_growth_yoy": 0.125}),
    ]
    metrics = [
        SectorMetric("ind_pe_median", "P/E trung vị ngành Bất động sản", 24.5, "x", "annual", "2025-01-01", "2025-12-31", ["ind_src_vietstock_bds_benchmark"], "median_peer_pe"),
        SectorMetric("ind_pb_median", "P/B trung vị ngành Bất động sản", 1.35, "x", "annual", "2025-01-01", "2025-12-31", ["ind_src_vietstock_bds_benchmark"], "median_peer_pb"),
        SectorMetric("ind_roe_avg", "ROE bình quân ngành Bất động sản", 0.0593, "ratio", "annual", "2025-01-01", "2025-12-31", ["ind_src_vietstock_bds_benchmark"], "mean_peer_roe"),
    ]
    findings = [
        SectorFinding("ind_f01_legal_framework_unlock", "Hiệu lực thực thi của 3 bộ luật (Luật Đất đai, Luật Nhà ở, Luật Kinh doanh BĐS) tháo gỡ điểm nghẽn phê duyệt pháp lý dự án, giúp khơi thông nguồn cung mới từ cuối năm 2026.", ["ind_src_vars_real_estate_2026"]),
    ]
    risks = [
        SectorRisk("ind_r01_bond_maturity_pressure", "Áp lực đáo hạn trái phiếu doanh nghiệp và dòng tiền thu tiền theo tiến độ xây dựng vẫn là bài toán sống còn đối với các chủ đầu tư đòn bẩy tài chính cao.", ["ind_src_vietstock_bds_benchmark"]),
    ]
    return SectorProfile("8630", "Bất động sản dân cư & Phát triển hạ tầng", "recovery", peers, metrics, findings, risks, sources)


def get_securities_sector(as_of_date: str = "2026-10-09") -> SectorProfile:
    sources = [
        SectorSource(
            source_id="ind_src_ssc_market_liquidity_2026",
            title="Ủy ban Chứng khoán Nhà nước (UBCKNN) - Báo cáo Thanh khoản thị trường và tiến độ triển khai hệ thống giao dịch mới KRX năm 2026",
            url="https://ssc.gov.vn/webcenter/portal/ubck/pages_r/l/tintucsukien/",
            published_at="2026-09-20",
            retrieved_at="2026-10-09T08:00:00+07:00",
            locator="Phần thống kê giá trị giao dịch bình quân phiên (ADTV) đạt 22.000 tỷ VND",
            publication_date_verified=True,
        ),
        SectorSource(
            source_id="ind_src_vietstock_sec_benchmark",
            title="Vietstock Finance - Báo cáo Định giá & Tỷ lệ dư nợ Margin toàn ngành Chứng khoán 2026",
            url="https://finance.vietstock.vn/nganh-nghe/8770/dich-vu-tai-chinh.htm",
            published_at="2026-09-30",
            retrieved_at="2026-10-09T08:15:00+07:00",
            locator="Bảng P/B, P/E, Margin/VCSH các CTCK niêm yết",
            publication_date_verified=True,
        ),
    ]
    peers = [
        PeerCompany("VCI", "CTCP Chứng khoán Vietcap", "HOSE", 23500000000000.0, "Thế mạnh số 1 thị trường về mảng tư vấn ngân hàng đầu tư (IB), bảo lãnh phát hành và khách hàng tổ chức nước ngoài.", {"pe": 16.5, "pb": 2.15, "roe": 0.155, "roa": 0.065, "net_margin": 0.385, "gross_margin": None, "debt_to_equity": 1.25, "revenue_growth_yoy": 0.285}),
        PeerCompany("VND", "CTCP Chứng khoán VNDIRECT", "HOSE", 22800000000000.0, "Quy mô vốn điều lệ và lượng khách hàng cá nhân giao dịch thuộc top 3 toàn thị trường, mảng công nghệ số mạnh.", {"pe": 13.8, "pb": 1.35, "roe": 0.125, "roa": 0.048, "net_margin": 0.325, "gross_margin": None, "debt_to_equity": 1.85, "revenue_growth_yoy": 0.165}),
        PeerCompany("HCM", "CTCP Chứng khoán Thành phố Hồ Chí Minh (HSC)", "HOSE", 21200000000000.0, "Cơ cấu tài chính an toàn tuyệt đối, thị phần môi giới top 3 và danh mục tự doanh thận trọng.", {"pe": 15.2, "pb": 1.85, "roe": 0.145, "roa": 0.058, "net_margin": 0.365, "gross_margin": None, "debt_to_equity": 1.45, "revenue_growth_yoy": 0.225}),
    ]
    metrics = [
        SectorMetric("ind_pe_median", "P/E trung vị ngành Chứng khoán", 15.2, "x", "annual", "2025-01-01", "2025-12-31", ["ind_src_vietstock_sec_benchmark"], "median_peer_pe"),
        SectorMetric("ind_pb_median", "P/B trung vị ngành Chứng khoán", 1.85, "x", "annual", "2025-01-01", "2025-12-31", ["ind_src_vietstock_sec_benchmark"], "median_peer_pb"),
        SectorMetric("ind_roe_avg", "ROE bình quân ngành Chứng khoán", 0.1417, "ratio", "annual", "2025-01-01", "2025-12-31", ["ind_src_vietstock_sec_benchmark"], "mean_peer_roe"),
    ]
    findings = [
        SectorFinding("ind_f01_upgrade_ftse_krx", "Triển vọng nâng hạng thị trường chứng khoán Việt Nam từ cận biên (Frontier) lên mới nổi thứ cấp (Secondary Emerging Market) của FTSE Russell cùng vận hành hệ thống KRX là cú hích thanh khoản mang tính chu kỳ lớn cho toàn bộ các CTCK.", ["ind_src_ssc_market_liquidity_2026"]),
    ]
    risks = [
        SectorRisk("ind_r01_market_volatility_fvtpl", "Biến động mạnh của chỉ số VN-Index ảnh hưởng trực tiếp đến kết quả đánh giá lại danh mục tài sản tài chính tự doanh (FVTPL) và thanh khoản dư nợ cho vay ký quỹ (Margin).", ["ind_src_vietstock_sec_benchmark"]),
    ]
    return SectorProfile("8770", "Dịch vụ tài chính & Chứng khoán", "expansion", peers, metrics, findings, risks, sources)
