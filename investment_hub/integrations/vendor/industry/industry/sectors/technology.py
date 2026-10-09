"""Sector data profile: Ngành Công nghệ thông tin & Viễn thông (ICB 9530).
Đã sửa theo kết quả rà soát phản biện ngày 09/10/2026:
- Tái lập chuẩn xác 100% benchmark từ 3 peers:
  + Median P/E: 16.8x (sắp xếp: 14.2, 16.8, 24.5)
  + Median P/B: 2.15x (sắp xếp: 1.25, 2.15, 3.85)
  + Mean ROE: 13.30%
- Bổ sung chỉ số biên ròng bình quân ngành: 7.30%
- Bổ sung metadata thời gian và kỳ tài chính cho toàn bộ peers.
- Điều chỉnh ngôn ngữ nhận định khách quan, loại bỏ các từ ngữ khẳng định tuyệt đối.
"""
from industry.sectors.base import (
    PeerCompany,
    SectorFinding,
    SectorMetric,
    SectorProfile,
    SectorRisk,
    SectorSource,
)


def get_technology_sector(as_of_date: str = "2026-10-09") -> SectorProfile:
    sources = [
        SectorSource(
            source_id="ind_src_vinasa_report_2026",
            title="Hiệp hội Phần mềm và Dịch vụ CNTT Việt Nam (VINASA) - Báo cáo Tổng quan Thị trường Công nghiệp ICT & Xuất khẩu phần mềm Việt Nam 2025-2026",
            url="https://vinasa.org.vn/bao-cao-nganh-ict-viet-nam/",
            published_at="2026-08-20",
            retrieved_at="2026-10-09T08:00:00+07:00",
            locator="Phần IV: Doanh thu dịch vụ phần mềm và xuất khẩu giải pháp số của doanh nghiệp Việt Nam",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Đối chiếu bản báo cáo tổng kết thường niên VINASA tháng 8/2026",
        ),
        SectorSource(
            source_id="ind_src_mic_stats_2026",
            title="Bộ Thông tin và Truyền thông (MIC) - Niên giám thống kê công nghiệp công nghệ số và viễn thông 8 tháng 2026",
            url="https://mic.gov.vn/so-lieu-thong-ke-nganh-thong-tin-va-truyen-thong/",
            published_at="2026-09-10",
            retrieved_at="2026-10-09T08:15:00+07:00",
            locator="Bảng 1.2: Doanh thu xuất khẩu dịch vụ CNTT và giải pháp số 8T/2026",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Số liệu công bố chính thức trên cổng thông tin MIC",
        ),
        SectorSource(
            source_id="ind_src_vietstock_tech_benchmark",
            title="Vietstock Finance - Báo cáo Định giá & Hiệu quả vốn ngành Công nghệ thông tin Việt Nam 2026",
            url="https://finance.vietstock.vn/nganh-nghe/9530/phan-mem-dich-vu-may-tinh.htm",
            published_at="2026-09-30",
            retrieved_at="2026-10-09T08:30:00+07:00",
            locator="Bảng thống kê P/E, P/B và ROE nhóm cổ phiếu CNTT niêm yết chốt phiên 30/09/2026",
            publication_date_verified=True,
            verified_by="Nguoi_2",
            verification_date="2026-10-09",
            verification_note="Dữ liệu giá chốt phiên 30/09/2026 và BCTC kiểm toán năm 2025",
        ),
    ]

    peers = [
        PeerCompany(
            ticker="CMG",
            name="CTCP Tập đoàn Công nghệ CMC",
            exchange="HOSE",
            market_cap=8950000000000.0,
            comparison_basis="Đối thủ lớn thứ 2 tại Việt Nam trong mảng chuyển đổi số doanh nghiệp, viễn thông và hạ tầng trung tâm dữ liệu (Data Center).",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=[],
            metrics={
                "pe": 24.5,
                "pb": 3.85,
                "roe": 0.165,
                "roa": 0.078,
                "net_margin": 0.082,
                "gross_margin": 0.215,
                "debt_to_equity": 0.45,
                "revenue_growth_yoy": 0.185,
            },
        ),
        PeerCompany(
            ticker="ELC",
            name="CTCP Công nghệ - Viễn thông Elcom",
            exchange="HOSE",
            market_cap=2150000000000.0,
            comparison_basis="Tập trung chuyên sâu vào giải pháp giao thông thông minh (ITS), viễn thông và an ninh số; hưởng lợi từ các dự án cao tốc quốc gia.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=[],
            metrics={
                "pe": 16.8,
                "pb": 2.15,
                "roe": 0.142,
                "roa": 0.085,
                "net_margin": 0.095,
                "gross_margin": 0.285,
                "debt_to_equity": 0.22,
                "revenue_growth_yoy": 0.245,
            },
        ),
        PeerCompany(
            ticker="ITD",
            name="CTCP Công nghệ Tiên Phong",
            exchange="HOSE",
            market_cap=680000000000.0,
            comparison_basis="Cung cấp giải pháp hạ tầng thông tin, tự động hóa và tích hợp hệ thống cho khối chính phủ và doanh nghiệp vừa.",
            valuation_date="2026-10-09",
            financial_period_end="2025-12-31",
            period_type="annual",
            statement_scope="consolidated",
            not_applicable_metrics=[],
            metrics={
                "pe": 14.2,
                "pb": 1.25,
                "roe": 0.092,
                "roa": 0.045,
                "net_margin": 0.042,
                "gross_margin": 0.185,
                "debt_to_equity": 0.35,
                "revenue_growth_yoy": 0.085,
            },
        ),
    ]

    metrics = [
        SectorMetric(
            metric_id="ind_pe_median",
            name="P/E trung vị nhóm so sánh (Peers Median P/E)",
            value=16.8,  # Sửa từ 20.65x thành 16.8x để tái lập chính xác 100% từ 3 peers (ITD 14.2, ELC 16.8, CMG 24.5)
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_tech_benchmark"],
            formula_id="median_peer_pe",
            sample_size=3,
            methodology_note="Trung vị của 3 peers: ITD (14.2), ELC (16.8), CMG (24.5) = 16.8x",
        ),
        SectorMetric(
            metric_id="ind_pb_median",
            name="P/B trung vị nhóm so sánh (Peers Median P/B)",
            value=2.15,  # Sửa từ 3.0x thành 2.15x để tái lập chính xác 100% từ 3 peers (ITD 1.25, ELC 2.15, CMG 3.85)
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_tech_benchmark"],
            formula_id="median_peer_pb",
            sample_size=3,
            methodology_note="Trung vị của 3 peers: ITD (1.25), ELC (2.15), CMG (3.85) = 2.15x",
        ),
        SectorMetric(
            metric_id="ind_roe_avg",
            name="ROE bình quân nhóm so sánh (Peers Mean ROE)",
            value=0.133,  # 13.30%
            unit="ratio",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_tech_benchmark"],
            formula_id="mean_peer_roe",
            sample_size=3,
            methodology_note="Trung bình cộng 3 peers: (0.165 + 0.142 + 0.092) / 3 = 0.133",
        ),
        SectorMetric(
            metric_id="ind_net_margin_avg",
            name="Biên lợi nhuận ròng bình quân nhóm so sánh",
            value=0.073,  # 7.30%
            unit="ratio",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_tech_benchmark"],
            formula_id="mean_peer_net_margin",
            sample_size=3,
            methodology_note="Trung bình cộng 3 peers: (0.082 + 0.095 + 0.042) / 3 = 0.073",
        ),
        SectorMetric(
            metric_id="ind_ict_export_growth",
            name="Tăng trưởng kim ngạch xuất khẩu dịch vụ CNTT 8T/2026 (YoY)",
            value=0.178,  # 17.8% YoY
            unit="ratio",
            frequency="monthly",
            period_start="2026-01-01",
            period_end="2026-08-31",
            source_refs=["ind_src_mic_stats_2026"],
            formula_id="mic_ict_export_yoy",
            methodology_note="Theo số liệu công bố lũy kế 8 tháng 2026 của Bộ Thông tin và Truyền thông",
        ),
    ]

    findings = [
        SectorFinding(
            finding_id="ind_f01_ai_digital_wave",
            text="Ngành Công nghệ thông tin Việt Nam duy trì đà tăng trưởng tích cực (Expansion Stage). Dữ liệu ngành 8 tháng 2026 cho thấy kim ngạch xuất khẩu dịch vụ CNTT tăng trưởng 17.8% YoY, dẫn dắt bởi nhu cầu chuyển đổi số doanh nghiệp, triển khai giải pháp điện toán đám mây và ứng dụng trí tuệ nhân tạo (AI) từ các thị trường quốc tế trọng điểm như Nhật Bản, Bắc Mỹ và khu vực Châu Á - Thái Bình Dương.",
            evidence_refs=["ind_src_vinasa_report_2026", "ind_ict_export_growth"],
            claim_type="observation",
            horizon="Trung hạn 6 - 12 tháng",
        ),
        SectorFinding(
            finding_id="ind_f02_cost_advantage_vietnam",
            text="Lợi thế nguồn nhân lực công nghệ số trẻ với chi phí cạnh tranh tiếp tục là bệ phóng giúp các doanh nghiệp phần mềm Việt Nam duy trì biên lợi nhuận hoạt động ổn định. Đối với các đơn vị đầu ngành có quy mô nhân sự lớn, việc tích lũy kinh nghiệm chuyên ngành (Domain Expertise) và đối tác công nghệ toàn cầu tạo điều kiện tiếp cận các gói thầu chuyển đổi số quy mô lớn.",
            evidence_refs=["ind_src_mic_stats_2026", "ind_net_margin_avg"],
            claim_type="mechanism",
            horizon="Dài hạn",
        ),
    ]

    risks = [
        SectorRisk(
            risk_id="ind_r01_macro_slowdown_abroad",
            text="Rủi ro biến động ngân sách chi tiêu công nghệ tại các thị trường xuất khẩu trọng điểm: Xuất khẩu phần mềm chịu ảnh hưởng gián tiếp nếu các tập đoàn đa quốc gia tại Mỹ hoặc Nhật Bản trì hoãn kế hoạch đầu tư hệ thống mới trong bối cảnh tăng trưởng kinh tế toàn cầu có sự phân hóa.",
            evidence_refs=["ind_src_vinasa_report_2026"],
            risk_category="market",
        ),
        SectorRisk(
            risk_id="ind_r02_fx_volatility_jpy_usd",
            text="Rủi ro biến động tỷ giá hối đoái đối với doanh thu ngoại tệ: Các hợp đồng phần mềm thanh toán bằng đồng Yên Nhật (JPY) hoặc USD có thể chịu ảnh hưởng chênh lệch tỷ giá kế toán nếu các đồng tiền này biến động mạnh so với VND mà chưa có công cụ phòng ngừa rủi ro tương ứng.",
            evidence_refs=["ind_src_vietstock_tech_benchmark"],
            risk_category="market",
        ),
    ]

    return SectorProfile(
        industry_code="9530",
        industry_name="Công nghệ thông tin & Viễn thông",
        sector_cycle_stage="expansion",
        peers=peers,
        metrics=metrics,
        findings=findings,
        risks=risks,
        sources=sources,
    )
