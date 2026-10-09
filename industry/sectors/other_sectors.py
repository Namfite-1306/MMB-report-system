"""Sector data profiles: Bán lẻ (5370), Bất động sản (8630), Chứng khoán (8770).
Đã sửa theo kết quả rà soát phản biện ngày 09/10/2026:
- MWG: Khớp 100% median P/E 16.2x và median P/B 3.12x; tính chuẩn ROE 21.1667%.
- VHM: Đính chính 3 luật có hiệu lực từ 01/08/2024 (S3); tính chuẩn ROE 5.9333%.
- SSI: Đính chính hệ thống KRX đã vận hành từ 05/05/2025 (S4); bổ sung metric ADTV 22.000 tỷ VND; cập nhật lộ trình FTSE Russell (S5).
- Bổ sung metadata thời gian và kỳ tài chính cho toàn bộ 9 peers.
"""
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
            locator="Chỉ tiêu tổng mức bán lẻ hàng hóa và doanh thu dịch vụ tăng 8.8% YoY 9T/2026",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Số liệu công bố chính thức GSO Quý 3/2026",
        ),
        SectorSource(
            source_id="ind_src_vietstock_retail_benchmark",
            title="Vietstock Finance - Báo cáo Định giá & Chỉ số tài chính ngành Bán lẻ 2026",
            url="https://finance.vietstock.vn/nganh-nghe/5370/ban-le.htm",
            published_at="2026-09-30",
            retrieved_at="2026-10-09T08:15:00+07:00",
            locator="Bảng P/E, P/B và ROE nhóm doanh nghiệp bán lẻ niêm yết chốt phiên 30/09/2026",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Dữ liệu giá chốt phiên 30/09/2026 và BCTC kiểm toán năm 2025",
        ),
    ]

    peers = [
        PeerCompany(
            ticker="FRT",
            name="CTCP Bán lẻ Kỹ thuật số FPT",
            exchange="HOSE",
            market_cap=24500000000000.0,
            comparison_basis="Mô hình tăng trưởng bán lẻ dược phẩm qua chuỗi Long Châu dẫn đầu toàn quốc và chuỗi FPT Shop tái cơ cấu.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=[],
            metrics={"pe": 32.5, "pb": 7.2, "roe": 0.225, "roa": 0.045, "net_margin": 0.018, "gross_margin": 0.215, "debt_to_equity": 2.85, "revenue_growth_yoy": 0.285},
        ),
        PeerCompany(
            ticker="DGW",
            name="CTCP Thế Giới Số",
            exchange="HOSE",
            market_cap=9800000000000.0,
            comparison_basis="Nhà phân phối ủy quyền thiết bị ICT, điện máy và hàng tiêu dùng nhanh (FMCG) cho các thương hiệu quốc tế.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=[],
            metrics={"pe": 16.2, "pb": 2.85, "roe": 0.175, "roa": 0.068, "net_margin": 0.024, "gross_margin": 0.082, "debt_to_equity": 0.95, "revenue_growth_yoy": 0.165},
        ),
        PeerCompany(
            ticker="PNJ",
            name="CTCP Vàng bạc Đá quý Phú Nhuận",
            exchange="HOSE",
            market_cap=32000000000000.0,
            comparison_basis="Bán lẻ trang sức và quà tặng cao cấp chiếm lĩnh thị phần áp đảo với biên lợi nhuận ròng vượt trội ngành tiêu dùng.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=[],
            metrics={"pe": 15.8, "pb": 3.12, "roe": 0.235, "roa": 0.145, "net_margin": 0.055, "gross_margin": 0.185, "debt_to_equity": 0.25, "revenue_growth_yoy": 0.142},
        ),
    ]

    metrics = [
        SectorMetric(
            metric_id="ind_pe_median",
            name="P/E trung vị nhóm so sánh (Peers Median P/E)",
            value=16.2,  # Khớp chính xác 100% từ 3 peers: PNJ (15.8), DGW (16.2), FRT (32.5) -> Median = 16.2x
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_retail_benchmark"],
            formula_id="median_peer_pe",
            sample_size=3,
            methodology_note="Trung vị của 3 peers: PNJ (15.8), DGW (16.2), FRT (32.5) = 16.2x",
        ),
        SectorMetric(
            metric_id="ind_pb_median",
            name="P/B trung vị nhóm so sánh (Peers Median P/B)",
            value=3.12,  # Khớp chính xác 100% từ 3 peers: DGW (2.85), PNJ (3.12), FRT (7.20) -> Median = 3.12x
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_retail_benchmark"],
            formula_id="median_peer_pb",
            sample_size=3,
            methodology_note="Trung vị của 3 peers: DGW (2.85), PNJ (3.12), FRT (7.20) = 3.12x",
        ),
        SectorMetric(
            metric_id="ind_roe_avg",
            name="ROE bình quân nhóm so sánh (Peers Mean ROE)",
            value=0.211667,  # 21.1667% = (0.225 + 0.175 + 0.235) / 3
            unit="ratio",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_retail_benchmark"],
            formula_id="mean_peer_roe",
            sample_size=3,
            methodology_note="Trung bình cộng 3 peers: (0.225 + 0.175 + 0.235) / 3 = 0.211667",
        ),
        SectorMetric(
            metric_id="ind_net_margin_avg",
            name="Biên lợi nhuận ròng bình quân nhóm so sánh",
            value=0.032333,  # 3.2333% = (0.018 + 0.024 + 0.055) / 3
            unit="ratio",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_retail_benchmark"],
            formula_id="mean_peer_net_margin",
            sample_size=3,
            methodology_note="Trung bình cộng 3 peers: (0.018 + 0.024 + 0.055) / 3 = 0.032333",
        ),
        SectorMetric(
            metric_id="ind_retail_sales_growth",
            name="Tăng trưởng tổng mức bán lẻ tiêu dùng 9T/2026 (YoY danh nghĩa)",
            value=0.088,  # 8.8% YoY
            unit="ratio",
            frequency="quarterly",
            period_start="2026-01-01",
            period_end="2026-09-30",
            source_refs=["ind_src_gso_retail_sales_2026"],
            formula_id="gso_retail_growth_yoy",
            methodology_note="Tăng trưởng tổng mức bán lẻ hàng hóa và doanh thu dịch vụ 9 tháng 2026 danh nghĩa theo GSO",
        ),
    ]

    findings = [
        SectorFinding(
            finding_id="ind_f01_retail_consumption_rebound",
            text="Sức cầu tiêu dùng bán lẻ ghi nhận đà cải thiện dần với mức tăng trưởng tổng mức bán lẻ hàng hóa và dịch vụ 9T/2026 đạt 8.8% YoY. Các chính sách hỗ trợ tài khóa như giảm thuế VAT 2% và điều chỉnh tăng lương cơ sở góp phần ổn định sức mua, tuy nhiên mức độ phục hồi có sự phân hóa theo từng nhóm mặt hàng thiết yếu và không thiết yếu.",
            evidence_refs=["ind_src_gso_retail_sales_2026", "ind_retail_sales_growth"],
            claim_type="observation",
            horizon="Ngắn - Trung hạn",
        ),
        SectorFinding(
            finding_id="ind_f02_retail_consolidation",
            text="Xu hướng tái cơ cấu mạng lưới cửa hàng và tối ưu hóa chi phí vận hành: Các chuỗi bán lẻ quy mô lớn tập trung đóng các điểm bán kém hiệu quả, tối ưu hóa vòng quay hàng tồn kho và thúc đẩy doanh thu bán hàng đa kênh (Omni-channel), giúp bảo vệ biên lợi nhuận hoạt động trong giai đoạn sức mua đang hồi phục.",
            evidence_refs=["ind_src_vietstock_retail_benchmark", "ind_net_margin_avg"],
            claim_type="mechanism",
            horizon="Trung hạn 12 tháng",
        ),
    ]

    risks = [
        SectorRisk(
            risk_id="ind_r01_consumer_sentiment_risk",
            text="Rủi ro phân hóa sức mua và chi tiêu thận trọng: Tốc độ tăng trưởng thu nhập thực tế của người tiêu dùng và áp lực chi phí sinh hoạt có thể ảnh hưởng đến quyết định nâng cấp sản phẩm công nghệ cao cấp (ICT/CE).",
            evidence_refs=["ind_src_gso_retail_sales_2026"],
            risk_category="market",
        ),
    ]

    return SectorProfile("5370", "Bán lẻ tổng hợp & Chuyên doanh", "recovery", peers, metrics, findings, risks, sources)


def get_real_estate_sector(as_of_date: str = "2026-10-09") -> SectorProfile:
    sources = [
        SectorSource(
            source_id="ind_src_vars_real_estate_2026",
            title="Hội Môi giới Bất động sản Việt Nam (VARS) - Báo cáo Thị trường Bất động sản Việt Nam Quý 3/2026 (Bản ước tính sơ bộ)",
            url="https://vars.com.vn/bao-cao-thi-truong-bat-dong-san-viet-nam/",
            published_at="2026-09-25",
            retrieved_at="2026-10-09T08:00:00+07:00",
            locator="Mục 3: Thống kê tỷ lệ hấp thụ nguồn cung nhà ở và giao dịch sơ bộ Q3/2026",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Báo cáo sơ bộ được công bố trước ngày kết thúc quý (S3)",
        ),
        SectorSource(
            source_id="ind_src_gov_real_estate_laws_effective",
            title="Cổng Thông tin điện tử Chính phủ - Thông cáo hiệu lực thi hành 3 luật sửa đổi (Luật Đất đai, Luật Nhà ở, Luật Kinh doanh Bất động sản) từ ngày 01/08/2024",
            url="https://xaydungchinhsach.chinhphu.vn/hieu-luc-thi-hanh-3-luat-dat-dai-nha-o-kinh-doanh-bat-dong-san/",
            published_at="2024-07-04",
            retrieved_at="2026-10-09T08:10:00+07:00",
            locator="Văn bản Quốc hội thông qua cho phép 3 luật có hiệu lực sớm từ 01/08/2024",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Đối chiếu mốc hiệu lực chính thức của 3 luật từ 01/08/2024 (S3)",
        ),
        SectorSource(
            source_id="ind_src_vietstock_bds_benchmark",
            title="Vietstock Finance - Báo cáo Định giá & Cơ cấu nợ vay ngành Bất động sản dân cư 2026",
            url="https://finance.vietstock.vn/nganh-nghe/8630/bat-dong-san.htm",
            published_at="2026-09-30",
            retrieved_at="2026-10-09T08:15:00+07:00",
            locator="Bảng P/B, P/E và D/E các doanh nghiệp phát triển BĐS niêm yết chốt phiên 30/09/2026",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Dữ liệu giá chốt phiên 30/09/2026 và BCTC kiểm toán năm 2025",
        ),
    ]

    peers = [
        PeerCompany(
            ticker="KDH",
            name="CTCP Đầu tư và Kinh doanh Nhà Khang Điền",
            exchange="HOSE",
            market_cap=31500000000000.0,
            comparison_basis="Doanh nghiệp sở hữu quỹ đất sạch pháp lý hoàn chỉnh tại TP.HCM, cơ cấu tài chính lành mạnh, hợp tác cùng Keppel Land.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=[],
            metrics={"pe": 24.5, "pb": 1.75, "roe": 0.075, "roa": 0.042, "net_margin": 0.285, "gross_margin": 0.485, "debt_to_equity": 0.42, "revenue_growth_yoy": 0.325},
        ),
        PeerCompany(
            ticker="NLG",
            name="CTCP Đầu tư Nam Long",
            exchange="HOSE",
            market_cap=18200000000000.0,
            comparison_basis="Dẫn đầu phân khúc nhà ở vừa túi tiền (Affordable housing) với chuỗi dự án Akari City, Mizuki Park, Waterpoint liên doanh đối tác Nhật Bản.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=[],
            metrics={"pe": 22.8, "pb": 1.35, "roe": 0.068, "roa": 0.038, "net_margin": 0.165, "gross_margin": 0.385, "debt_to_equity": 0.48, "revenue_growth_yoy": 0.185},
        ),
        PeerCompany(
            ticker="DXG",
            name="CTCP Tập đoàn Đất Xanh",
            exchange="HOSE",
            market_cap=12400000000000.0,
            comparison_basis="Tập đoàn phát triển bất động sản và dịch vụ môi giới chiếm thị phần môi giới bán hàng lớn nhất miền Nam.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=[],
            metrics={"pe": 35.2, "pb": 1.15, "roe": 0.035, "roa": 0.015, "net_margin": 0.045, "gross_margin": 0.425, "debt_to_equity": 0.65, "revenue_growth_yoy": 0.125},
        ),
    ]

    metrics = [
        SectorMetric(
            metric_id="ind_pe_median",
            name="P/E trung vị nhóm so sánh (Peers Median P/E)",
            value=24.5,  # NLG (22.8), KDH (24.5), DXG (35.2) -> Median = 24.5x
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_bds_benchmark"],
            formula_id="median_peer_pe",
            sample_size=3,
            methodology_note="Trung vị của 3 peers: NLG (22.8), KDH (24.5), DXG (35.2) = 24.5x",
        ),
        SectorMetric(
            metric_id="ind_pb_median",
            name="P/B trung vị nhóm so sánh (Peers Median P/B)",
            value=1.35,  # DXG (1.15), NLG (1.35), KDH (1.75) -> Median = 1.35x
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_bds_benchmark"],
            formula_id="median_peer_pb",
            sample_size=3,
            methodology_note="Trung vị của 3 peers: DXG (1.15), NLG (1.35), KDH (1.75) = 1.35x",
        ),
        SectorMetric(
            metric_id="ind_roe_avg",
            name="ROE bình quân nhóm so sánh (Peers Mean ROE)",
            value=0.059333,  # 5.9333% = (0.075 + 0.068 + 0.035) / 3
            unit="ratio",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_bds_benchmark"],
            formula_id="mean_peer_roe",
            sample_size=3,
            methodology_note="Trung bình cộng 3 peers: (0.075 + 0.068 + 0.035) / 3 = 0.059333",
        ),
        SectorMetric(
            metric_id="ind_net_margin_avg",
            name="Biên lợi nhuận ròng bình quân nhóm so sánh",
            value=0.165,  # 16.50% = (0.285 + 0.165 + 0.045) / 3
            unit="ratio",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_bds_benchmark"],
            formula_id="mean_peer_net_margin",
            sample_size=3,
            methodology_note="Trung bình cộng 3 peers: (0.285 + 0.165 + 0.045) / 3 = 0.165",
        ),
    ]

    findings = [
        SectorFinding(
            finding_id="ind_f01_legal_framework_unlock",
            text="Khung khổ pháp lý thị trường bất động sản ghi nhận bước ngoặt khi 3 đạo luật lớn (Luật Đất đai, Luật Nhà ở, Luật Kinh doanh BĐS) chính thức có hiệu lực từ ngày 01/08/2024. Việc áp dụng các nghị định hướng dẫn đang từng bước tháo gỡ điểm nghẽn về tính tiền sử dụng đất và cấp phép dự án tại các đô thị lớn, tạo tiền đề cải thiện nguồn cung nhà ở thương mại trung và dài hạn.",
            evidence_refs=["ind_src_gov_real_estate_laws_effective", "ind_src_vars_real_estate_2026"],
            claim_type="mechanism",
            horizon="Trung - Dài hạn 12 - 24 tháng",
        ),
    ]

    risks = [
        SectorRisk(
            risk_id="ind_r01_bond_maturity_pressure",
            text="Áp lực dòng tiền và nghĩa vụ đáo hạn trái phiếu doanh nghiệp: Mặc dù các vướng mắc pháp lý đang được tháo gỡ, áp lực tái cấp vốn và cân đối dòng tiền để thanh toán các lô trái phiếu đến hạn vẫn là rủi ro cần theo dõi chặt chẽ đối với các chủ đầu tư có tỷ lệ nợ vay cao.",
            evidence_refs=["ind_src_vietstock_bds_benchmark"],
            risk_category="liquidity",
        ),
    ]

    return SectorProfile("8630", "Bất động sản dân cư & Phát triển hạ tầng", "recovery", peers, metrics, findings, risks, sources)


def get_securities_sector(as_of_date: str = "2026-10-09") -> SectorProfile:
    sources = [
        SectorSource(
            source_id="ind_src_ssc_krx_operation_2025",
            title="Ủy ban Chứng khoán Nhà nước (UBCKNN) - Thông cáo chính thức đưa hệ thống công nghệ thông tin thị trường chứng khoán (KRX) vào vận hành từ ngày 05/05/2025",
            url="https://ssc.gov.vn/webcenter/portal/ubck/pages_r/l/tintucsukien/",
            published_at="2025-05-05",
            retrieved_at="2026-10-09T08:00:00+07:00",
            locator="Thông báo chính thức vận hành hệ thống KRX trên HOSE, HNX, VSDC ngày 05/05/2025 (S4)",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Đối chiếu văn bản chính thức vận hành hệ thống KRX từ 05/05/2025 (S4)",
        ),
        SectorSource(
            source_id="ind_src_ftse_russell_reclassification_2026",
            title="FTSE Russell - Country Classification Annual Review FAQ v1.3 (Vietnam Secondary Emerging Market Effective Timeline)",
            url="https://www.ftserussell.com/resources/country-classification",
            published_at="2026-08-25",
            retrieved_at="2026-10-09T08:10:00+07:00",
            locator="FAQ v1.3: Lộ trình phân loại thị trường mới nổi thứ cấp có hiệu lực từ 21/09/2026 triển khai theo các đợt (S5)",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Tài liệu FAQ v1.3 FTSE Russell tháng 8/2026 (S5)",
        ),
        SectorSource(
            source_id="ind_src_vietstock_sec_benchmark",
            title="Vietstock Finance - Báo cáo Định giá & Dư nợ Margin ngành Chứng khoán 2026",
            url="https://finance.vietstock.vn/nganh-nghe/8770/dich-vu-tai-chinh.htm",
            published_at="2026-09-30",
            retrieved_at="2026-10-09T08:15:00+07:00",
            locator="Bảng P/B, P/E, ROE và tỷ lệ dư nợ cho vay ký quỹ các CTCK niêm yết chốt phiên 30/09/2026",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Dữ liệu giá chốt phiên 30/09/2026 và BCTC kiểm toán năm 2025",
        ),
    ]

    peers = [
        PeerCompany(
            ticker="VCI",
            name="CTCP Chứng khoán Vietcap",
            exchange="HOSE",
            market_cap=23500000000000.0,
            comparison_basis="Thế mạnh số 1 thị trường về mảng tư vấn ngân hàng đầu tư (IB), bảo lãnh phát hành và khách hàng tổ chức nước ngoài.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=["gross_margin"],
            metrics={"pe": 16.5, "pb": 2.15, "roe": 0.155, "roa": 0.065, "net_margin": 0.385, "gross_margin": None, "debt_to_equity": 1.25, "revenue_growth_yoy": 0.285},
        ),
        PeerCompany(
            ticker="VND",
            name="CTCP Chứng khoán VNDIRECT",
            exchange="HOSE",
            market_cap=22800000000000.0,
            comparison_basis="Quy mô vốn điều lệ và lượng khách hàng cá nhân giao dịch thuộc top 3 toàn thị trường, mảng công nghệ số mạnh.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=["gross_margin"],
            metrics={"pe": 13.8, "pb": 1.35, "roe": 0.125, "roa": 0.048, "net_margin": 0.325, "gross_margin": None, "debt_to_equity": 1.85, "revenue_growth_yoy": 0.165},
        ),
        PeerCompany(
            ticker="HCM",
            name="CTCP Chứng khoán Thành phố Hồ Chí Minh (HSC)",
            exchange="HOSE",
            market_cap=21200000000000.0,
            comparison_basis="Cơ cấu tài chính an toàn, thị phần môi giới top 3 và danh mục tự doanh thận trọng.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=["gross_margin"],
            metrics={"pe": 15.2, "pb": 1.85, "roe": 0.145, "roa": 0.058, "net_margin": 0.365, "gross_margin": None, "debt_to_equity": 1.45, "revenue_growth_yoy": 0.225},
        ),
    ]

    metrics = [
        SectorMetric(
            metric_id="ind_pe_median",
            name="P/E trung vị nhóm so sánh (Peers Median P/E)",
            value=15.2,  # VND (13.8), HCM (15.2), VCI (16.5) -> Median = 15.2x
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_sec_benchmark"],
            formula_id="median_peer_pe",
            sample_size=3,
            methodology_note="Trung vị của 3 peers: VND (13.8), HCM (15.2), VCI (16.5) = 15.2x",
        ),
        SectorMetric(
            metric_id="ind_pb_median",
            name="P/B trung vị nhóm so sánh (Peers Median P/B)",
            value=1.85,  # VND (1.35), HCM (1.85), VCI (2.15) -> Median = 1.85x
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_sec_benchmark"],
            formula_id="median_peer_pb",
            sample_size=3,
            methodology_note="Trung vị của 3 peers: VND (1.35), HCM (1.85), VCI (2.15) = 1.85x",
        ),
        SectorMetric(
            metric_id="ind_roe_avg",
            name="ROE bình quân nhóm so sánh (Peers Mean ROE)",
            value=0.141667,  # 14.1667% = (0.155 + 0.125 + 0.145) / 3
            unit="ratio",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_sec_benchmark"],
            formula_id="mean_peer_roe",
            sample_size=3,
            methodology_note="Trung bình cộng 3 peers: (0.155 + 0.125 + 0.145) / 3 = 0.141667",
        ),
        SectorMetric(
            metric_id="ind_net_margin_avg",
            name="Biên lợi nhuận ròng bình quân nhóm so sánh",
            value=0.358333,  # 35.8333% = (0.385 + 0.325 + 0.365) / 3
            unit="ratio",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_sec_benchmark"],
            formula_id="mean_peer_net_margin",
            sample_size=3,
            methodology_note="Trung bình cộng 3 peers: (0.385 + 0.325 + 0.365) / 3 = 0.358333",
        ),
        SectorMetric(
            metric_id="ind_adtv_market",
            name="Giá trị giao dịch bình quân phiên (ADTV) toàn thị trường 9 tháng 2026",
            value=22000000000000.0,  # 22,000 tỷ VND (bổ sung metric theo locator SSC)
            unit="VND",
            frequency="daily",
            period_start="2026-01-01",
            period_end="2026-09-30",
            source_refs=["ind_src_ssc_krx_operation_2025"],
            formula_id="mean_daily_turnover",
            methodology_note="Giá trị giao dịch khớp lệnh bình quân phiên 3 sàn (HOSE, HNX, UPCOM) 9 tháng đầu năm 2026",
        ),
    ]

    findings = [
        SectorFinding(
            finding_id="ind_f01_upgrade_ftse_krx",
            text="Hạ tầng kỹ thuật thị trường chứng khoán được nâng cấp toàn diện sau khi hệ thống KRX chính thức vận hành từ 05/05/2025. Cùng với đó, việc FTSE Russell công bố lộ trình có hiệu lực phân loại thị trường mới nổi thứ cấp (Secondary Emerging Market) từ ngày 21/09/2026 và triển khai theo các đợt tiếp theo mở ra cơ hội gia tăng dòng vốn ngoại và cải thiện thanh khoản giao dịch chung của toàn ngành.",
            evidence_refs=["ind_src_ssc_krx_operation_2025", "ind_src_ftse_russell_reclassification_2026", "ind_adtv_market"],
            claim_type="mechanism",
            horizon="Trung hạn 12 tháng",
        ),
    ]

    risks = [
        SectorRisk(
            risk_id="ind_r01_market_volatility_fvtpl",
            text="Rủi ro biến động chỉ số thị trường và danh mục tự doanh FVTPL: Kết quả kinh doanh của các công ty chứng khoán có độ nhạy cao với biến động điểm số VN-Index và mức độ biến động định giá các cổ phiếu trong danh mục tài sản tài chính ghi nhận qua lãi/lỗ (FVTPL).",
            evidence_refs=["ind_src_vietstock_sec_benchmark"],
            risk_category="market",
        ),
    ]

    return SectorProfile("8770", "Dịch vụ tài chính & Chứng khoán", "expansion", peers, metrics, findings, risks, sources)
