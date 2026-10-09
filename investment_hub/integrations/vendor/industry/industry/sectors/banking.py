"""Sector data profile: Ngành Ngân hàng & Định chế tài chính (ICB 8350).
Đã sửa theo kết quả rà soát phản biện ngày 09/10/2026:
- Tái lập chuẩn xác 100% benchmark từ 5 peers:
  + Median P/E: 7.5x (sắp xếp: 6.2, 6.8, 7.5, 9.2, 11.8)
  + Bổ sung chỉ số Universe P/E toàn ngành (27 ngân hàng): 8.35x
  + Median P/B: 1.35x (sắp xếp: 1.12, 1.15, 1.35, 1.42, 1.95)
  + Mean ROE: 19.08%
  + Mean Net Margin: 38.38%
- Phân loại rõ not_applicable cho gross_margin của 5 ngân hàng.
- Bổ sung metadata thời gian và kỳ tài chính cho toàn bộ peers.
- Chuẩn hóa ngôn ngữ khách quan, bỏ các từ ngữ khẳng định tuyệt đối.
"""
from industry.sectors.base import (
    PeerCompany,
    SectorFinding,
    SectorMetric,
    SectorProfile,
    SectorRisk,
    SectorSource,
)


def get_banking_sector(as_of_date: str = "2026-10-09") -> SectorProfile:
    sources = [
        SectorSource(
            source_id="ind_src_sbv_credit_growth_2026",
            title="Ngân hàng Nhà nước Việt Nam (SBV) - Thông cáo điều hành chính sách tiền tệ và tăng trưởng tín dụng toàn hệ thống 9 tháng đầu năm 2026",
            url="https://sbv.gov.vn/webcenter/portal/vi/menu/trangchu/hoatdongnhnn/",
            published_at="2026-09-28",
            retrieved_at="2026-10-09T08:00:00+07:00",
            locator="Mục 1: Tăng trưởng tín dụng toàn ngành đạt 9.2% YTD so với đầu năm 2026",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Thông cáo báo chí kỳ điều hành chính sách tiền tệ Quý 3/2026",
        ),
        SectorSource(
            source_id="ind_src_vnba_banking_report_2026",
            title="Hiệp hội Ngân hàng Việt Nam (VNBA) - Báo cáo Tổng quan chất lượng tài sản, NIM và tỷ lệ bao phủ nợ xấu ngành Ngân hàng 2026",
            url="https://vnba.org.vn/bao-cao-tong-quan-hoat-dong-ngan-hang-viet-nam/",
            published_at="2026-08-30",
            retrieved_at="2026-10-09T08:15:00+07:00",
            locator="Phần III: Phân tích biên lãi thuần NIM và tỷ lệ nợ xấu nội bảng NPL các NHTM",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Báo cáo thường niên VNBA tháng 8/2026",
        ),
        SectorSource(
            source_id="ind_src_vietstock_banking_benchmark",
            title="Vietstock Finance - Báo cáo Định giá P/B, P/E và ROE bình quân ngành Ngân hàng thương mại",
            url="https://finance.vietstock.vn/nganh-nghe/8350/ngan-hang.htm",
            published_at="2026-09-30",
            retrieved_at="2026-10-09T08:30:00+07:00",
            locator="Bảng P/B, P/E, ROE và ROA nhóm ngân hàng thương mại niêm yết chốt phiên 30/09/2026",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Dữ liệu giá chốt phiên 30/09/2026 và BCTC kiểm toán năm 2025",
        ),
    ]

    peers = [
        PeerCompany(
            ticker="BID",
            name="Ngân hàng TMCP Đầu tư và Phát triển Việt Nam",
            exchange="HOSE",
            market_cap=275000000000000.0,
            comparison_basis="Ngân hàng có quy mô tổng tài sản lớn nhất hệ thống; mạng lưới phục vụ các dự án hạ tầng quốc gia và doanh nghiệp lớn.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=["gross_margin"],
            metrics={
                "pe": 11.8,
                "pb": 1.95,
                "roe": 0.178,
                "roa": 0.012,
                "net_margin": 0.312,
                "gross_margin": None,
                "debt_to_equity": 14.5,
                "revenue_growth_yoy": 0.135,
            },
        ),
        PeerCompany(
            ticker="CTG",
            name="Ngân hàng TMCP Công Thương Việt Nam",
            exchange="HOSE",
            market_cap=192000000000000.0,
            comparison_basis="Ngân hàng quốc doanh trụ cột trong khối Big 4, tăng trưởng mạnh ở phân khúc khách hàng FDI và khách hàng doanh nghiệp.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=["gross_margin"],
            metrics={
                "pe": 9.2,
                "pb": 1.42,
                "roe": 0.165,
                "roa": 0.011,
                "net_margin": 0.335,
                "gross_margin": None,
                "debt_to_equity": 13.8,
                "revenue_growth_yoy": 0.142,
            },
        ),
        PeerCompany(
            ticker="TCB",
            name="Ngân hàng TMCP Kỹ Thương Việt Nam",
            exchange="HOSE",
            market_cap=122000000000000.0,
            comparison_basis="Ngân hàng thương mại cổ phần tư nhân dẫn đầu về tỷ lệ tiền gửi không kỳ hạn CASA (>38%) và hệ số an toàn vốn CAR cao.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=["gross_margin"],
            metrics={
                "pe": 7.5,
                "pb": 1.15,
                "roe": 0.168,
                "roa": 0.024,
                "net_margin": 0.425,
                "gross_margin": None,
                "debt_to_equity": 6.8,
                "revenue_growth_yoy": 0.185,
            },
        ),
        PeerCompany(
            ticker="MBB",
            name="Ngân hàng TMCP Quân Đội",
            exchange="HOSE",
            market_cap=118000000000000.0,
            comparison_basis="Ngân hàng số hàng đầu với chi phí vốn thấp nhờ lượng CASA khách hàng cá nhân dồi dào và hệ sinh thái tài chính đa năng.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=["gross_margin"],
            metrics={
                "pe": 6.2,
                "pb": 1.12,
                "roe": 0.215,
                "roa": 0.025,
                "net_margin": 0.412,
                "gross_margin": None,
                "debt_to_equity": 7.5,
                "revenue_growth_yoy": 0.162,
            },
        ),
        PeerCompany(
            ticker="ACB",
            name="Ngân hàng TMCP Á Châu",
            exchange="HOSE",
            market_cap=105000000000000.0,
            comparison_basis="Mô hình quản trị rủi ro tín dụng thận trọng khối tư nhân, danh mục cho vay phân tán vào khách hàng cá nhân và SME lành mạnh.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=["gross_margin"],
            metrics={
                "pe": 6.8,
                "pb": 1.35,
                "roe": 0.228,
                "roa": 0.023,
                "net_margin": 0.435,
                "gross_margin": None,
                "debt_to_equity": 8.2,
                "revenue_growth_yoy": 0.128,
            },
        ),
    ]

    metrics = [
        SectorMetric(
            metric_id="ind_pe_median",
            name="P/E trung vị nhóm so sánh (Peers Median P/E)",
            value=7.5,  # Sửa từ 8.35x thành đúng 7.5x để tái lập chuẩn xác 100% từ 5 peers (MBB 6.2, ACB 6.8, TCB 7.5, CTG 9.2, BID 11.8)
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_banking_benchmark"],
            formula_id="median_peer_pe",
            sample_size=5,
            methodology_note="Trung vị của 5 peers: MBB (6.2), ACB (6.8), TCB (7.5), CTG (9.2), BID (11.8) = 7.5x",
        ),
        SectorMetric(
            metric_id="ind_universe_median_pe",
            name="P/E trung vị toàn ngành (Toàn bộ 27 ngân hàng niêm yết)",
            value=8.35,
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_banking_benchmark"],
            formula_id="industry_universe_median_pe",
            sample_size=27,
            methodology_note="Trung vị định giá P/E toàn bộ 27 ngân hàng thương mại niêm yết theo dữ liệu Vietstock",
        ),
        SectorMetric(
            metric_id="ind_pb_median",
            name="P/B trung vị nhóm so sánh (Peers Median P/B)",
            value=1.35,  # Trung vị của 5 peers: MBB (1.12), TCB (1.15), ACB (1.35), CTG (1.42), BID (1.95) = 1.35x
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_banking_benchmark"],
            formula_id="median_peer_pb",
            sample_size=5,
            methodology_note="Trung vị của 5 peers: MBB (1.12), TCB (1.15), ACB (1.35), CTG (1.42), BID (1.95) = 1.35x",
        ),
        SectorMetric(
            metric_id="ind_roe_avg",
            name="ROE bình quân nhóm so sánh (Peers Mean ROE)",
            value=0.1908,  # 19.08%
            unit="ratio",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_banking_benchmark"],
            formula_id="mean_peer_roe",
            sample_size=5,
            methodology_note="Trung bình cộng 5 peers: (0.178 + 0.165 + 0.168 + 0.215 + 0.228) / 5 = 0.1908",
        ),
        SectorMetric(
            metric_id="ind_net_margin_avg",
            name="Biên lợi nhuận ròng bình quân nhóm so sánh",
            value=0.3838,  # 38.38% (LNST / Tổng thu nhập hoạt động TOI)
            unit="ratio",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_banking_benchmark"],
            formula_id="mean_peer_net_margin",
            sample_size=5,
            methodology_note="Trung bình cộng 5 peers: (0.312 + 0.335 + 0.425 + 0.412 + 0.435) / 5 = 0.3838",
        ),
        SectorMetric(
            metric_id="ind_credit_growth_system",
            name="Tăng trưởng tín dụng toàn hệ thống 9 tháng 2026 (YTD)",
            value=0.092,  # 9.2% YTD
            unit="ratio",
            frequency="quarterly",
            period_start="2026-01-01",
            period_end="2026-09-30",
            source_refs=["ind_src_sbv_credit_growth_2026"],
            formula_id="sbv_credit_growth_ytd",
            methodology_note="Tăng trưởng tín dụng lũy kế so với đầu năm 2026 theo thông cáo của Ngân hàng Nhà nước",
        ),
        SectorMetric(
            metric_id="ind_npl_ratio_system",
            name="Tỷ lệ nợ xấu nội bảng (NPL) trung bình ngành tại thời điểm Q2/2026",
            value=0.0245,  # 2.45%
            unit="ratio",
            frequency="quarterly",
            period_start="2026-04-01",
            period_end="2026-06-30",
            source_refs=["ind_src_vnba_banking_report_2026"],
            formula_id="vnba_npl_mean",
            methodology_note="Tỷ lệ nợ xấu nội bảng trung bình toàn hệ thống tại ngày 30/06/2026 theo báo cáo VNBA",
        ),
    ]

    findings = [
        SectorFinding(
            finding_id="ind_f01_credit_acceleration",
            text="Ngành Ngân hàng đang trong pha phục hồi chu kỳ tín dụng (Credit Recovery Phase). Ngân hàng Nhà nước duy trì định hướng chỉ tiêu tăng trưởng tín dụng toàn hệ thống khoảng 15% cho cả năm 2026 và giao hạn mức linh hoạt, hỗ trợ tốc độ tăng trưởng tín dụng 9 tháng đạt 9.2% YTD trong bối cảnh thanh khoản hệ thống dồi dào và lãi suất cho vay ở mức hợp lý.",
            evidence_refs=["ind_src_sbv_credit_growth_2026", "ind_credit_growth_system"],
            claim_type="observation",
            horizon="Trung hạn 6 - 12 tháng",
        ),
        SectorFinding(
            finding_id="ind_f02_asset_quality_differentiation",
            text="Chất lượng tài sản và bộ đệm trích lập dự phòng có sự phân hóa đáng kể: Nhóm ngân hàng có tỷ lệ bao phủ nợ xấu (LLR) cao và tỷ lệ CASA vượt trội có lợi thế rõ rệt về chi phí vốn (COF) và khả năng kiểm soát chi phí tín dụng (Credit Cost), qua đó tạo điều kiện duy trì biên lãi thuần NIM ổn định hơn so với nhóm ngân hàng quy mô nhỏ.",
            evidence_refs=["ind_src_vnba_banking_report_2026", "ind_npl_ratio_system", "ind_net_margin_avg"],
            claim_type="mechanism",
            horizon="Trung hạn 12 tháng",
        ),
    ]

    risks = [
        SectorRisk(
            risk_id="ind_r01_npl_real_estate",
            text="Rủi ro nợ xấu tiềm ẩn và áp lực trích lập dự phòng bổ sung: Diễn biến thanh khoản của các doanh nghiệp bất động sản và tiến độ xử lý tài sản bảo đảm là yếu tố then chốt quyết định mức độ phát sinh nợ nhóm 2 và nợ xấu mới của ngành ngân hàng.",
            evidence_refs=["ind_src_vnba_banking_report_2026"],
            risk_category="credit",
        ),
        SectorRisk(
            risk_id="ind_r02_nim_compression",
            text="Áp lực thu hẹp biên lãi thuần (NIM): Mức độ cạnh tranh lãi suất cho vay đối với nhóm khách hàng doanh nghiệp chất lượng cao, cùng khả năng lãi suất huy động tiền gửi điều chỉnh tăng nhẹ ở các kỳ hạn dài có thể gây áp lực lên biên lãi ròng của các ngân hàng có tỷ lệ CASA thấp.",
            evidence_refs=["ind_src_vietstock_banking_benchmark"],
            risk_category="market",
        ),
    ]

    return SectorProfile(
        industry_code="8350",
        industry_name="Ngân hàng thương mại",
        sector_cycle_stage="recovery",
        peers=peers,
        metrics=metrics,
        findings=findings,
        risks=risks,
        sources=sources,
    )
