"""Sector data profile: Ngành Thép & Vật liệu xây dựng (ICB 1750).
Đã sửa theo kết quả rà soát phản biện ngày 09/10/2026:
- Sửa chính xác ngày ban hành QĐ 1985/QĐ-BCT: 26/07/2024 (S1).
- Bổ sung Quyết định 1959/QĐ-BCT ngày 04/07/2025 áp thuế chống bán phá giá chính thức cho HRC Trung Quốc (S2).
- Khớp số ROE bình quân peers: 0.08425 (8.425%).
- Bổ sung metadata thời gian và kỳ BCTC cho toàn bộ peers.
"""
from industry.sectors.base import (
    PeerCompany,
    SectorFinding,
    SectorMetric,
    SectorProfile,
    SectorRisk,
    SectorSource,
)


def get_steel_sector(as_of_date: str = "2026-10-09") -> SectorProfile:
    # 1. Danh sách nguồn kiểm chứng chính thức (đã đối soát ngày văn bản gốc)
    sources = [
        SectorSource(
            source_id="ind_src_vsa_report_2026",
            title="Hiệp hội Thép Việt Nam (VSA) - Báo cáo tổng kết tình hình sản xuất và bán hàng thép xây dựng, HRC 8 tháng đầu năm 2026",
            url="http://vsa.com.vn/tinh-hinh-san-xuat-va-tieu-thu-thep-viet-nam/",
            published_at="2026-09-15",
            retrieved_at="2026-10-09T08:00:00+07:00",
            locator="Mục 2.1 & 2.3: Sản lượng bán hàng HRC và thép xây dựng toàn ngành 8T/2026",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Đối chiếu số liệu báo cáo bản tin tháng 8/2026 của VSA",
        ),
        SectorSource(
            source_id="ind_src_gso_industry_q3_2026",
            title="Tổng cục Thống kê (GSO) - Báo cáo Tình hình kinh tế - xã hội 9 tháng năm 2026 (Chỉ số sản xuất công nghiệp IIP ngành sản xuất kim loại)",
            url="https://www.gso.gov.vn/du-lieu-va-so-lieu-thong-ke/2026/09/tinh-hinh-kinh-te-xa-hoi-9-thang-nam-2026/",
            published_at="2026-09-29",
            retrieved_at="2026-10-09T08:15:00+07:00",
            locator="Biểu số 4: Chỉ số sản xuất ngành sản xuất kim loại (Ngành cấp 2 mã 24)",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Đối chiếu Niên giám số liệu kinh tế - xã hội Quý 3/2026 GSO",
        ),
        SectorSource(
            source_id="ind_src_moit_ad20_decision_1985",
            title="Bộ Công Thương - Quyết định số 1985/QĐ-BCT ngày 26/07/2024 về việc điều tra áp dụng biện pháp chống bán phá giá đối với thép cán nóng (HRC) từ Trung Quốc và Ấn Độ",
            url="http://trav.gov.vn/thong-bao-dieu-tra-chong-ban-pha-gia-hrc.html",
            published_at="2024-07-26",
            retrieved_at="2026-10-09T08:30:00+07:00",
            locator="Quyết định 1985/QĐ-BCT, Cục Phòng vệ thương mại",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Đã đính chính năm ban hành văn bản chính thức là 2024 (S1)",
        ),
        SectorSource(
            source_id="ind_src_moit_ad20_decision_1959",
            title="Bộ Công Thương - Quyết định số 1959/QĐ-BCT ngày 04/07/2025 áp dụng thuế chống bán phá giá chính thức đối với một số sản phẩm thép cuộn cán nóng (HRC) xuất xứ Trung Quốc và chấm dứt điều tra đối với Ấn Độ",
            url="http://trav.gov.vn/quyet-dinh-ap-thue-chong-ban-pha-gia-hrc-1959.html",
            published_at="2025-07-04",
            retrieved_at="2026-10-09T08:35:00+07:00",
            locator="Quyết định 1959/QĐ-BCT ngày 04/07/2025 và Thông báo ngày 08/07/2025",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Bổ sung văn bản kết luận chính thức vụ việc AD20 (S2, S2a)",
        ),
        SectorSource(
            source_id="ind_src_vietstock_steel_benchmark",
            title="Vietstock Finance - Báo cáo Tổng quan định giá và chỉ số tài chính ngành Vật liệu xây dựng & Thép năm 2025-2026",
            url="https://finance.vietstock.vn/nganh-nghe/1750/san-xuat-thep.htm",
            published_at="2026-09-30",
            retrieved_at="2026-10-09T08:45:00+07:00",
            locator="Bảng thống kê định giá P/E, P/B và ROE các doanh nghiệp ngành Thép",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Dữ liệu giá chốt phiên 30/09/2026 và BCTC kiểm toán năm 2025",
        ),
    ]

    # 2. Doanh nghiệp cùng ngành (Peers) có đầy đủ metadata thời gian & kỳ kế toán
    peers = [
        PeerCompany(
            ticker="NKG",
            name="CTCP Thép Nam Kim",
            exchange="HOSE",
            market_cap=5820000000000.0,
            comparison_basis="Cùng phân khúc tôn mạ và thép cuộn xuất khẩu; biên lợi nhuận phụ thuộc lớn vào giá HRC đầu vào.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=[],
            metrics={
                "pe": 12.8,
                "pb": 1.12,
                "roe": 0.089,
                "roa": 0.041,
                "net_margin": 0.028,
                "gross_margin": 0.075,
                "debt_to_equity": 0.95,
                "revenue_growth_yoy": 0.142,
            },
        ),
        PeerCompany(
            ticker="HSG",
            name="CTCP Tập đoàn Hoa Sen",
            exchange="HOSE",
            market_cap=12450000000000.0,
            comparison_basis="Doanh nghiệp chiếm thị phần tôn mạ số 1 Việt Nam (khoảng 28-30%); hệ thống phân phối bán lẻ Hoa Sen Home rộng khắp.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=[],
            metrics={
                "pe": 14.5,
                "pb": 1.25,
                "roe": 0.098,
                "roa": 0.048,
                "net_margin": 0.032,
                "gross_margin": 0.112,
                "debt_to_equity": 0.72,
                "revenue_growth_yoy": 0.115,
            },
        ),
        PeerCompany(
            ticker="VGS",
            name="CTCP Ống thép Việt Đức",
            exchange="HNX",
            market_cap=3120000000000.0,
            comparison_basis="Chuyên về sản phẩm ống thép xây dựng và kết cấu thép miền Bắc; hưởng lợi lớn từ sóng giải ngân đầu tư công hạ tầng.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=[],
            metrics={
                "pe": 15.2,
                "pb": 1.48,
                "roe": 0.115,
                "roa": 0.052,
                "net_margin": 0.038,
                "gross_margin": 0.089,
                "debt_to_equity": 0.88,
                "revenue_growth_yoy": 0.168,
            },
        ),
        PeerCompany(
            ticker="TVN",
            name="Tổng Công ty Thép Việt Nam - CTCP",
            exchange="UPCOM",
            market_cap=6150000000000.0,
            comparison_basis="Tập đoàn quốc doanh sản xuất phôi thép và thép xây dựng truyền thống; năng lực công nghệ và biên lợi nhuận thấp hơn khối tư nhân.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=[],
            metrics={
                "pe": 18.6,
                "pb": 0.65,
                "roe": 0.035,
                "roa": 0.014,
                "net_margin": 0.012,
                "gross_margin": 0.045,
                "debt_to_equity": 1.15,
                "revenue_growth_yoy": 0.062,
            },
        ),
    ]

    # 3. Các chỉ số vĩ mô ngành và benchmark tái lập từ peers
    metrics = [
        SectorMetric(
            metric_id="ind_pe_median",
            name="P/E trung vị nhóm so sánh (Peers Median P/E)",
            value=14.85,
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_steel_benchmark"],
            formula_id="median_peer_pe",
            sample_size=4,
            methodology_note="Trung vị của 4 peers: NKG (12.8), HSG (14.5), VGS (15.2), TVN (18.6) = (14.5 + 15.2) / 2 = 14.85x",
        ),
        SectorMetric(
            metric_id="ind_pb_median",
            name="P/B trung vị nhóm so sánh (Peers Median P/B)",
            value=1.185,
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_steel_benchmark"],
            formula_id="median_peer_pb",
            sample_size=4,
            methodology_note="Trung vị của 4 peers: TVN (0.65), NKG (1.12), HSG (1.25), VGS (1.48) = (1.12 + 1.25) / 2 = 1.185x",
        ),
        SectorMetric(
            metric_id="ind_roe_avg",
            name="ROE bình quân nhóm so sánh (Peers Mean ROE)",
            value=0.08425,  # 8.425% (khớp số học chính xác tuyệt đối, tránh sai số làm tròn 8.4%)
            unit="ratio",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_steel_benchmark"],
            formula_id="mean_peer_roe",
            sample_size=4,
            methodology_note="Trung bình cộng 4 peers: (0.089 + 0.098 + 0.115 + 0.035) / 4 = 0.08425",
        ),
        SectorMetric(
            metric_id="ind_net_margin_avg",
            name="Biên lợi nhuận ròng bình quân nhóm so sánh",
            value=0.0275,  # 2.75%
            unit="ratio",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_steel_benchmark"],
            formula_id="mean_peer_net_margin",
            sample_size=4,
            methodology_note="Trung bình cộng 4 peers: (0.028 + 0.032 + 0.038 + 0.012) / 4 = 0.0275",
        ),
        SectorMetric(
            metric_id="ind_crude_steel_consumption_growth",
            name="Tăng trưởng bán hàng thép xây dựng & HRC toàn ngành 8T/2026 (YoY)",
            value=0.118,  # 11.8%
            unit="ratio",
            frequency="monthly",
            period_start="2026-01-01",
            period_end="2026-08-31",
            source_refs=["ind_src_vsa_report_2026"],
            formula_id="vsa_yoy_sales_growth",
            methodology_note="Lũy kế sản lượng bán hàng 8 tháng 2026 so với cùng kỳ 2025 theo báo cáo VSA",
        ),
        SectorMetric(
            metric_id="ind_iip_metal_growth",
            name="Chỉ số IIP sản xuất kim loại 9 tháng 2026 (YoY)",
            value=0.106,  # 10.6%
            unit="ratio",
            frequency="quarterly",
            period_start="2026-01-01",
            period_end="2026-09-30",
            source_refs=["ind_src_gso_industry_q3_2026"],
            formula_id="gso_iip_metal_yoy",
            methodology_note="Chỉ số sản xuất công nghiệp IIP ngành sản xuất kim loại cấp 2 (mã 24) theo GSO",
        ),
    ]

    # 4. Nhận định ngành (Findings) - điều chỉnh ngôn ngữ khách quan, tách bạch quan sát và cơ chế
    findings = [
        SectorFinding(
            finding_id="ind_f01_steel_recovery",
            text="Ngành thép đang trong pha phục hồi chu kỳ (Recovery Phase). Quan sát từ dữ liệu cho thấy tăng trưởng tiêu thụ thép xây dựng và HRC đạt 11.8% YoY trong 8T/2026 cùng chỉ số IIP sản xuất kim loại tăng 10.6% YoY. Cơ chế hỗ trợ chính đến từ tiến độ giải ngân đầu tư công các dự án đại hạ tầng giao thông và số lượng dự án nhà ở hoàn thành các bước pháp lý sơ bộ sau khi các luật sửa đổi có hiệu lực từ tháng 8/2024.",
            evidence_refs=["ind_src_vsa_report_2026", "ind_crude_steel_consumption_growth", "ind_iip_metal_growth"],
            claim_type="observation",
            horizon="Trung hạn 6 - 12 tháng",
        ),
        SectorFinding(
            finding_id="ind_f02_trade_defense",
            text="Chính sách phòng vệ thương mại có bước tiến then chốt khi Bộ Công Thương ban hành Quyết định 1959/QĐ-BCT ngày 04/07/2025 áp dụng biện pháp chống bán phá giá chính thức đối với một số sản phẩm thép cuộn cán nóng (HRC) nhập khẩu từ Trung Quốc. Quyết định này giúp hạn chế tình trạng bán phá giá và tạo điều kiện ổn định thị phần tiêu thụ nội địa cho các nhà sản xuất thép cán nóng trong nước.",
            evidence_refs=["ind_src_moit_ad20_decision_1985", "ind_src_moit_ad20_decision_1959"],
            claim_type="mechanism",
            horizon="Trung hạn 12 - 24 tháng",
        ),
        SectorFinding(
            finding_id="ind_f03_competitive_moat",
            text="Khảo sát cấu trúc ngành cho thấy lợi thế quy mô rõ rệt: Các tổ hợp lò cao khép kín BOF (như dự án Dung Quất của Hòa Phát) có lợi thế cạnh tranh về giá thành sản xuất phôi thép và HRC so với công nghệ lò điện EAF phế liệu nhỏ lẻ, nhờ khả năng tối ưu hóa nhiệt luyện liên tục và đàm phán giá quặng sắt/than cốc khối lượng lớn.",
            evidence_refs=["ind_src_vietstock_steel_benchmark", "ind_net_margin_avg"],
            claim_type="observation",
            horizon="Dài hạn",
        ),
    ]

    # 5. Rủi ro ngành (Risks)
    risks = [
        SectorRisk(
            risk_id="ind_r01_raw_material_volatility",
            text="Biến động giá nguyên vật liệu thượng nguồn toàn cầu: Giá quặng sắt và than mỡ luyện cốc thế giới chiếm tỷ trọng lớn trong cơ cấu chi phí sản xuất phôi. Biến động nguồn cung từ các mỏ khai thác tại Úc và Brazil có thể tạo áp lực trực tiếp lên biên lợi nhuận gộp của các doanh nghiệp luyện kim.",
            evidence_refs=["ind_src_vsa_report_2026"],
            risk_category="raw_material",
        ),
        SectorRisk(
            risk_id="ind_r02_dumping_pressure",
            text="Rủi ro cạnh tranh thương mại và kiểm soát nguồn gốc xuất xứ: Áp lực dư thừa công suất sản xuất thép từ khu vực và nguy cơ gian lận xuất xứ hàng hóa xuất khẩu có thể dẫn tới các cuộc điều tra tự vệ mới từ các thị trường nhập khẩu lớn (Mỹ, EU).",
            evidence_refs=["ind_src_moit_ad20_decision_1959"],
            risk_category="regulatory",
        ),
        SectorRisk(
            risk_id="ind_r03_carbon_green_transition",
            text="Thách thức tuân thủ lộ trình chuyển đổi phát thải carbon thấp và cơ chế CBAM: Các tiêu chuẩn báo cáo phát thải khí nhà kính đối với thép xuất khẩu đòi hỏi doanh nghiệp phải bố trí vốn đầu tư công nghệ giảm phát thải (Green Steel) trong trung và dài hạn.",
            evidence_refs=["ind_src_vietstock_steel_benchmark"],
            risk_category="regulatory",
        ),
    ]

    return SectorProfile(
        industry_code="1750",
        industry_name="Sản xuất Thép & Kim loại",
        sector_cycle_stage="recovery",
        peers=peers,
        metrics=metrics,
        findings=findings,
        risks=risks,
        sources=sources,
    )
