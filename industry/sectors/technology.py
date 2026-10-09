"""Sector data profile: Ngành Công nghệ thông tin & Viễn thông (ICB 9530).
Phục vụ phân tích cổ phiếu FPT và các doanh nghiệp trong ngành phần mềm/chuyển đổi số.
Dữ liệu kiểm chứng từ VINASA, Bộ Thông tin và Truyền thông (MIC) và BCTC kiểm toán.
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
            locator="Phần IV: Doanh thu dịch vụ phần mềm và chuyển đổi số toàn cầu của DN Việt Nam",
            publication_date_verified=True,
        ),
        SectorSource(
            source_id="ind_src_mic_stats_2026",
            title="Bộ Thông tin và Truyền thông (MIC) - Niên giám thống kê công nghiệp công nghệ số và viễn thông 8 tháng 2026",
            url="https://mic.gov.vn/so-lieu-thong-ke-nganh-thong-tin-va-truyen-thong/",
            published_at="2026-09-10",
            retrieved_at="2026-10-09T08:15:00+07:00",
            locator="Bảng 1.2: Doanh thu xuất khẩu dịch vụ CNTT và giải pháp số",
            publication_date_verified=True,
        ),
        SectorSource(
            source_id="ind_src_vietstock_tech_benchmark",
            title="Vietstock Finance - Báo cáo Định giá & Hiệu quả vốn ngành Công nghệ thông tin Việt Nam 2026",
            url="https://finance.vietstock.vn/nganh-nghe/9530/phan-mem-dich-vu-may-tinh.htm",
            published_at="2026-09-30",
            retrieved_at="2026-10-09T08:30:00+07:00",
            locator="Bảng P/E, P/B và ROE bình quân ngành Công nghệ",
            publication_date_verified=True,
        ),
    ]

    peers = [
        PeerCompany(
            ticker="CMG",
            name="CTCP Tập đoàn Công nghệ CMC",
            exchange="HOSE",
            market_cap=8950000000000.0,  # 8,950 tỷ VND
            comparison_basis="Đối thủ lớn thứ 2 tại Việt Nam trong mảng chuyển đổi số doanh nghiệp, viễn thông và hạ tầng trung tâm dữ liệu (Data Center).",
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
            market_cap=2150000000000.0,  # 2,150 tỷ VND
            comparison_basis="Tập trung chuyên sâu vào giải pháp giao thông thông minh (ITS), viễn thông và an ninh số; hưởng lợi từ các dự án cao tốc quốc gia.",
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
            market_cap=680000000000.0,  # 680 tỷ VND
            comparison_basis="Cung cấp giải pháp hạ tầng thông tin, tự động hóa và tích hợp hệ thống cho khối chính phủ và doanh nghiệp vừa.",
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
            name="P/E trung vị ngành Công nghệ",
            value=20.65,
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_tech_benchmark"],
            formula_id="median_peer_pe",
        ),
        SectorMetric(
            metric_id="ind_pb_median",
            name="P/B trung vị ngành Công nghệ",
            value=3.0,
            unit="x",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_tech_benchmark"],
            formula_id="median_peer_pb",
        ),
        SectorMetric(
            metric_id="ind_roe_avg",
            name="ROE bình quân ngành Công nghệ",
            value=0.133,  # 13.3%
            unit="ratio",
            frequency="annual",
            period_start="2025-01-01",
            period_end="2025-12-31",
            source_refs=["ind_src_vietstock_tech_benchmark"],
            formula_id="mean_peer_roe",
        ),
        SectorMetric(
            metric_id="ind_ict_export_growth",
            name="Tăng trưởng kim ngạch xuất khẩu phần mềm & dịch vụ CNTT 8T/2026",
            value=0.178,  # 17.8% YoY
            unit="ratio",
            frequency="monthly",
            period_start="2026-01-01",
            period_end="2026-08-31",
            source_refs=["ind_src_mic_stats_2026"],
            formula_id="mic_ict_export_yoy",
        ),
    ]

    findings = [
        SectorFinding(
            finding_id="ind_f01_ai_digital_wave",
            text="Ngành Công nghệ thông tin Việt Nam đang ở pha tăng trưởng mở rộng (Expansion Stage) mạnh mẽ nhất trong thập kỷ. Làn sóng ứng dụng Trí tuệ nhân tạo (GenAI), điện toán đám mây và nhu cầu chuyển đổi số toàn cầu từ các thị trường trọng điểm (Nhật Bản, Bắc Mỹ, Châu Âu, APAC) thúc đẩy hợp đồng ký mới tăng trưởng hai chữ số bền vững.",
            evidence_refs=["ind_src_vinasa_report_2026", "ind_ict_export_growth"],
        ),
        SectorFinding(
            finding_id="ind_f02_cost_advantage_vietnam",
            text="Lợi thế chi phí nhân lực công nghệ thông tin và tháp dân số trẻ của Việt Nam tiếp tục là điểm tựa cạnh tranh xuất sắc so với Ấn Độ và Đông Âu. Doanh nghiệp đầu ngành như FPT có khả năng mở rộng quy mô hợp đồng lên cấp độ Mega-deal (>100 triệu USD) nhờ năng lực cung ứng trọn gói từ tư vấn chiến lược đến triển khai giải pháp chuyên sâu.",
            evidence_refs=["ind_src_mic_stats_2026"],
        ),
    ]

    risks = [
        SectorRisk(
            risk_id="ind_r01_macro_slowdown_abroad",
            text="Rủi ro suy thoái kinh tế hoặc cắt giảm ngân sách IT tại các thị trường trọng điểm: Doanh nghiệp xuất khẩu phần mềm phụ thuộc lớn vào chi tiêu công nghệ tại Mỹ và Nhật Bản. Nếu lãi suất neo cao kéo dài làm các tập đoàn đa quốc gia thắt chặt ngân sách R&D/IT sẽ ảnh hưởng đến tốc độ tăng trưởng ký mới hợp đồng.",
            evidence_refs=["ind_src_vinasa_report_2026"],
        ),
        SectorRisk(
            risk_id="ind_r02_fx_volatility_jpy_usd",
            text="Biến động tỷ giá hối đoái: Tỷ trọng doanh thu lớn từ đồng Yên Nhật (JPY) và USD tiềm ẩn rủi ro chênh lệch tỷ giá kế toán khi đồng JPY suy yếu hoặc biến động mạnh so với VND.",
            evidence_refs=["ind_src_vietstock_tech_benchmark"],
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
