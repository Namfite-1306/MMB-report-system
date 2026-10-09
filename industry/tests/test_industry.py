"""Test suite for Người 2 (Module Ngành - Industry Module).
Kiểm tra toàn diện tính tuân thủ hợp đồng dữ liệu Input/Output V1 và các tiêu chí phản biện:
- Benchmark tái lập chính xác 100% từ danh sách peers
- Đầy đủ metadata thời gian cho từng peer (valuation_date, financial_period_end, period_type, statement_scope)
- Nguồn đã đối soát ngày văn bản gốc (S1: QĐ 1985 năm 2024, S2: QĐ 1959 năm 2025, S3: 3 luật 2024, S4: KRX 2025, S5: FTSE 2026)
"""
import unittest

from industry.analyzer import analyze_industry, build_pending_industry_output
from industry.schema import validate_industry_output


class TestIndustryModule(unittest.TestCase):

    def test_pending_output(self):
        """Kiểm tra output khung rỗng pending khi làm việc song song."""
        pending = build_pending_industry_output(run_id="run_test_01", ticker="HPG", as_of_date="2026-10-09")
        self.assertEqual(pending["schema_version"], "1.0")
        self.assertEqual(pending["module"], "industry")
        self.assertEqual(pending["status"], "pending")
        self.assertEqual(pending["ticker"], "HPG")
        self.assertIn("+07:00", pending["generated_at"])
        self.assertEqual(pending["data"]["peers"], [])
        self.assertEqual(pending["data"]["metrics"], [])
        is_valid, errors = validate_industry_output(pending)
        self.assertTrue(is_valid, f"Pending output vi phạm schema: {errors}")

    def test_benchmark_reproducibility(self):
        """Kiểm tra khả năng tái lập 100% benchmark từ danh sách peers theo feedback."""
        cases = [
            ("HPG", 14.85, 1.185, 0.08425),
            ("FPT", 16.8, 2.15, 0.133),
            ("VCB", 7.5, 1.35, 0.1908),
            ("MWG", 16.2, 3.12, 0.211667),
            ("VHM", 24.5, 1.35, 0.059333),
            ("SSI", 15.2, 1.85, 0.141667),
        ]
        for ticker, exp_pe, exp_pb, exp_roe in cases:
            res = analyze_industry({"ticker": ticker, "as_of_date": "2026-10-09"})
            self.assertEqual(res["status"], "ok")
            metrics_dict = {m["metric_id"]: m["value"] for m in res["data"]["metrics"]}
            
            self.assertAlmostEqual(metrics_dict.get("ind_pe_median"), exp_pe, places=2, msg=f"Lệch P/E median của {ticker}")
            self.assertAlmostEqual(metrics_dict.get("ind_pb_median"), exp_pb, places=2, msg=f"Lệch P/B median của {ticker}")
            self.assertAlmostEqual(metrics_dict.get("ind_roe_avg"), exp_roe, places=4, msg=f"Lệch ROE avg của {ticker}")

    def test_peer_temporal_metadata(self):
        """Kiểm tra 21 peers có đủ metadata thời gian: valuation_date, financial_period_end, period_type, statement_scope."""
        for ticker in ["HPG", "FPT", "VCB", "MWG", "VHM", "SSI"]:
            res = analyze_industry({"ticker": ticker, "as_of_date": "2026-10-09"})
            for peer in res["data"]["peers"]:
                self.assertIn("valuation_date", peer)
                self.assertEqual(peer["valuation_date"], "2026-10-09")
                self.assertIn("financial_period_end", peer)
                self.assertIn("period_type", peer)
                self.assertIn("statement_scope", peer)
                self.assertIn("not_applicable_metrics", peer)

            # Kiểm tra ngân hàng và chứng khoán có đánh dấu not_applicable cho gross_margin
            if ticker in ["VCB", "SSI"]:
                for peer in res["data"]["peers"]:
                    self.assertIn("gross_margin", peer["not_applicable_metrics"])
                    self.assertIsNone(peer["metrics"]["gross_margin"])

    def test_verified_official_sources_dates(self):
        """Kiểm tra các mốc văn bản chính thức đã sửa theo phản biện S1-S5."""
        # 1. Thép: S1 (QĐ 1985 năm 2024), S2 (QĐ 1959 năm 2025)
        res_hpg = analyze_industry({"ticker": "HPG", "as_of_date": "2026-10-09"})
        src_map_hpg = {s["source_id"]: s for s in res_hpg["sources"]}
        self.assertIn("ind_src_moit_ad20_decision_1985", src_map_hpg)
        self.assertEqual(src_map_hpg["ind_src_moit_ad20_decision_1985"]["published_at"], "2024-07-26", "QĐ 1985 phải là năm 2024")
        self.assertIn("ind_src_moit_ad20_decision_1959", src_map_hpg)
        self.assertEqual(src_map_hpg["ind_src_moit_ad20_decision_1959"]["published_at"], "2025-07-04", "QĐ 1959 phải là năm 2025")

        # 2. Bất động sản: S3 (3 luật có hiệu lực 01/08/2024)
        res_vhm = analyze_industry({"ticker": "VHM", "as_of_date": "2026-10-09"})
        src_map_vhm = {s["source_id"]: s for s in res_vhm["sources"]}
        self.assertIn("ind_src_gov_real_estate_laws_effective", src_map_vhm)
        self.assertEqual(src_map_vhm["ind_src_gov_real_estate_laws_effective"]["published_at"], "2024-07-04")

        # 3. Chứng khoán: S4 (KRX vận hành 05/05/2025), S5 (FTSE 21/09/2026)
        res_ssi = analyze_industry({"ticker": "SSI", "as_of_date": "2026-10-09"})
        src_map_ssi = {s["source_id"]: s for s in res_ssi["sources"]}
        self.assertIn("ind_src_ssc_krx_operation_2025", src_map_ssi)
        self.assertEqual(src_map_ssi["ind_src_ssc_krx_operation_2025"]["published_at"], "2025-05-05")
        self.assertIn("ind_src_ftse_russell_reclassification_2026", src_map_ssi)
        # Kiểm tra metric ADTV 22.000 tỷ VND được bổ sung
        metric_ids_ssi = {m["metric_id"]: m["value"] for m in res_ssi["data"]["metrics"]}
        self.assertIn("ind_adtv_market", metric_ids_ssi)
        self.assertEqual(metric_ids_ssi["ind_adtv_market"], 22000000000000.0)

    def test_data_conventions_strict(self):
        """Kiểm tra tuân thủ 100% hợp đồng dữ liệu chung V1."""
        for ticker in ["HPG", "FPT", "VCB", "MWG", "VHM", "SSI"]:
            res = analyze_industry({"ticker": ticker, "as_of_date": "2026-10-09"})
            is_valid, errors = validate_industry_output(res)
            self.assertTrue(is_valid, f"Output {ticker} vi phạm schema: {errors}")


if __name__ == "__main__":
    unittest.main()
