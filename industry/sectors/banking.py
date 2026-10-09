"""Sector data profile: Ngành Ngân hàng & Định chế tài chính (ICB 8350).
Phục vụ phân tích cổ phiếu VCB (Vietcombank) và các ngân hàng thương mại niêm yết.
Dữ liệu kiểm chứng từ Ngân hàng Nhà nước Việt Nam (SBV), Hiệp hội Ngân hàng (VNBA) và BCTC kiểm toán.
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
            locator="Mục 1: Tăng trưởng tín dụng toàn ngành đạt 9.2% so với đầu năm",
            publication_date_verified=True,
        ),
        SectorSource(
            source_id="ind_src_vnba_banking_report_2026",
            title="Hiệp hội Ngân hàng Việt Nam (VNBA) - Báo cáo Tổng quan chất lượng tài sản, NIM và tỷ lệ bao phủ nợ xấu ngành Ngân hàng 2026",
            url="https://vnba.org.vn/bao-cao-tong-quan-hoat-dong-ngan-hang-viet-nam/",
            published_at="2026-08-30",
            retrieved_at="2026-10-09T08:15:00+07:00",
            locator="Phần III: Phân tích biên lãi thuần NIM và tỷ lệ nợ xấu nội bảng NPL",
            publication_date_verified=True,
        ),
        SectorSource(
            source_id="ind_src_vietstock_banking_benchmark",
            title="Vietstock Finance - Báo cáo Định giá P/B, P/E và ROE bình quân ngành Ngân hàng thương mại",
            url="https://finance.vietstock.vn/nganh-nghe/8350/ngan-hang.htm",
            published_at="2026-09-30",
            retrieved_at="2026-10-09T08:30:00+07:00",
            locator="Bảng P/B, P/E, ROE và ROA 27 ngân hàng niêm yết",
            publication_date_verified=True,
        ),
    ]

    peers = [
        PeerCompany(
            ticker="BID",
            name="Ngân hàng TMCP Đầu tư và Phát triển Việt Nam",
            exchange="HOSE",
            market_cap=275000000000000.0,  # 275,000 tỷ VND
            comparison_basis="Ngân hàng có quy mô tổng tài sản lớn nhất hệ thống; tập trung mạng lưới phục vụ các dự án trọng điểm quốc gia và doanh nghiệp lớn.",
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
            market_cap=192000000000000.0,  # 192,000 tỷ VND
            comparison_basis="Ngân hàng quốc doanh trụ cột trong khối Big 4, tăng trưởng mạnh ở phân khúc khách hàng FDI và bán lẻ tiêu dùng.",
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
            market_cap=122000000000000.0,  # 122,000 tỷ VND
            comparison_basis="Ngân hàng thương mại cổ phần tư nhân dẫn đầu về tỷ lệ tiền gửi không kỳ hạn CASA (>40%) và hệ số an toàn vốn CAR chuẩn Basel II/III.",
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
            market_cap=118000000000000.0,  # 118,000 tỷ VND
            comparison_basis="Ngân hàng số hàng đầu với chi phí vốn thấp nhờ lượng CASA khách hàng cá nhân khổng lồ và hệ sinh thái tài chính đa năng (bảo hiểm, chứng khoán).",
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
            market_cap=105000000000000.0,  # 105,000 tỷ VND
            comparison_basis="Mô hình quản trị rủi ro tín dụng thận trọng nhất khối tư nhân, danh mục cho vay phân tán tuyệt đối vào khách hàng cá nhân và SME sạch.",
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
            name="P/E trung vị ngành Ngân hàng",
            value=8.35,
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_banking_benchmark"],
            formula_id="median_peer_pe",
        ),
        SectorMetric(
            metric_id="ind_pb_median",
            name="P/B trung vị ngành Ngân hàng",
            value=1.35,
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_banking_benchmark"],
            formula_id="median_peer_pb",
        ),
        SectorMetric(
            metric_id="ind_roe_avg",
            name="ROE bình quân ngành Ngân hàng",
            value=0.1908,  # 19.08%
            unit="ratio",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_banking_benchmark"],
            formula_id="mean_peer_roe",
        ),
        SectorMetric(
            metric_id="ind_credit_growth_system",
            name="Tăng trưởng tín dụng toàn hệ thống 9 tháng 2026",
            value=0.092,  # 9.2%
            unit="ratio",
            frequency="quarterly",
            period_start="2026-01-01",
            period_end="2026-09-30",
            source_refs=["ind_src_sbv_credit_growth_2026"],
            formula_id="sbv_credit_growth_ytd",
        ),
        SectorMetric(
            metric_id="ind_npl_ratio_system",
            name="Tỷ lệ nợ xấu nội bảng (NPL) trung bình ngành",
            value=0.0245,  # 2.45%
            unit="ratio",
            frequency="quarterly",
            period_start="2026-01-01",
            period_end="2026-06-30",
            source_refs=["ind_src_vnba_banking_report_2026"],
            formula_id="vnba_npl_mean",
        ),
    ]

    findings = [
        SectorFinding(
            finding_id="ind_f01_credit_acceleration",
            text="Ngành Ngân hàng đang trong pha tăng tốc chu kỳ tín dụng (Credit Acceleration Phase). Ngân hàng Nhà nước chủ động giao toàn bộ hạn mức room tín dụng 15% ngay từ đầu năm cùng định hướng duy trì mặt bằng lãi suất cho vay thấp để thúc đẩy sản xuất kinh doanh, giúp tăng trưởng tín dụng phục hồi vững chắc.",
            evidence_refs=["ind_src_sbv_credit_growth_2026", "ind_credit_growth_system"],
        ),
        SectorFinding(
            finding_id="ind_f02_asset_quality_differentiation",
            text="Sự phân hóa rõ nét về chất lượng tài sản và chi phí dự phòng: Các ngân hàng có tỷ lệ bao phủ nợ xấu (LLR) cao vượt trội (như Vietcombank đạt trên 200%) có bộ đệm trích lập an toàn tuyệt đối, giúp chủ động hoàn nhập dự phòng và duy trì đà tăng trưởng lợi nhuận trước thuế bền vững so với các ngân hàng nhỏ lẻ.",
            evidence_refs=["ind_src_vnba_banking_report_2026", "ind_npl_ratio_system"],
        ),
    ]

    risks = [
        SectorRisk(
            risk_id="ind_r01_npl_real_estate",
            text="Rủi ro nợ xấu tiềm ẩn và tái cơ cấu nợ: Mặc dù Thông tư giãn hoãn nợ hỗ trợ doanh nghiệp vượt qua giai đoạn khó khăn, nhưng áp lực nợ xấu chuyển nhóm vẫn là yếu tố cần theo dõi chặt chẽ nếu thanh khoản thị trường trái phiếu doanh nghiệp và bất động sản phục hồi chậm hơn kỳ vọng.",
            evidence_refs=["ind_src_vnba_banking_report_2026"],
        ),
        SectorRisk(
            risk_id="ind_r02_nim_compression",
            text="Áp lực thu hẹp biên lãi thuần (NIM): Cạnh tranh gay gắt về lãi suất cho vay đầu ra để giành thị phần khách hàng chất lượng cao trong khi lãi suất huy động đầu vào có dấu hiệu chạm đáy và nhích nhẹ.",
            evidence_refs=["ind_src_vietstock_banking_benchmark"],
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
