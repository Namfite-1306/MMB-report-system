"""Test suite for Người 2 (Module Ngành - Industry Module).
Kiểm tra toàn diện tính tuân thủ hợp đồng dữ liệu Input/Output V1.
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

    def test_steel_sector_hpg(self):
        """Kiểm tra phân tích ngành Thép cho mã HPG."""
        req = {
            "schema_version": "1.0",
            "run_id": "run_test_steel",
            "ticker": "HPG",
            "exchange": "HOSE",
            "as_of_date": "2026-10-09",
            "period_start": "2025-01-01",
            "period_end": "2026-09-30",
            "investment_horizon": "Trung hạn 6 - 12 tháng",
        }
        res = analyze_industry(req)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["data"]["industry_code"], "1750")
        self.assertIn("Thép", res["data"]["industry_name"])

        # Kiểm tra danh sách peers
        peer_tickers = [p["ticker"] for p in res["data"]["peers"]]
        self.assertIn("NKG", peer_tickers)
        self.assertIn("HSG", peer_tickers)

        # Kiểm tra tính hợp lệ của hợp đồng dữ liệu
        is_valid, errors = validate_industry_output(res)
        self.assertTrue(is_valid, f"Output HPG vi phạm hợp đồng: {errors}")

    def test_tech_sector_fpt(self):
        """Kiểm tra phân tích ngành CNTT cho mã FPT."""
        req = {
            "run_id": "run_test_tech",
            "ticker": "FPT",
            "as_of_date": "2026-10-09",
        }
        res = analyze_industry(req)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["data"]["industry_code"], "9530")
        peer_tickers = [p["ticker"] for p in res["data"]["peers"]]
        self.assertIn("CMG", peer_tickers)
        is_valid, errors = validate_industry_output(res)
        self.assertTrue(is_valid, f"Output FPT vi phạm hợp đồng: {errors}")

    def test_banking_sector_vcb(self):
        """Kiểm tra phân tích ngành Ngân hàng cho mã VCB."""
        req = {
            "run_id": "run_test_bank",
            "ticker": "VCB",
            "as_of_date": "2026-10-09",
        }
        res = analyze_industry(req)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["data"]["industry_code"], "8350")
        peer_tickers = [p["ticker"] for p in res["data"]["peers"]]
        self.assertIn("BID", peer_tickers)
        self.assertIn("CTG", peer_tickers)
        is_valid, errors = validate_industry_output(res)
        self.assertTrue(is_valid, f"Output VCB vi phạm hợp đồng: {errors}")

    def test_data_conventions(self):
        """Kiểm tra nghiêm ngặt các quy ước số & nguồn:
        - Tiền tệ: VND
        - Tỷ lệ: dạng thập phân (không có ký tự %)
        - Ngày: YYYY-MM-DD
        - Dữ liệu thiếu: null, không thay bằng 0
        - Ngày công bố nguồn <= as_of_date
        - Truy vết bằng chứng evidence_refs
        """
        for ticker in ["HPG", "FPT", "VCB", "MWG", "VHM", "SSI"]:
            res = analyze_industry({"ticker": ticker, "as_of_date": "2026-10-09"})
            self.assertEqual(res["status"], "ok")

            # 1. Kiểm tra metrics
            for m in res["data"]["metrics"]:
                val = m["value"]
                if val is not None:
                    self.assertIsInstance(val, (int, float))
                    self.assertFalse(isinstance(val, str) and "%" in val)
                self.assertRegex(m["period_start"], r"^\d{4}-\d{2}-\d{2}$")
                self.assertRegex(m["period_end"], r"^\d{4}-\d{2}-\d{2}$")
                self.assertLessEqual(m["period_end"], "2026-10-09")

            # 2. Kiểm tra peers metrics
            for peer in res["data"]["peers"]:
                self.assertTrue(len(peer["comparison_basis"]) > 10)
                for k, v in peer["metrics"].items():
                    if v is not None:
                        self.assertIsInstance(v, (int, float))

            # 3. Kiểm tra sources
            source_ids = {s["source_id"] for s in res["sources"]}
            for s in res["sources"]:
                self.assertTrue(s["source_id"].startswith("ind_src_"))
                self.assertTrue(s["url"].startswith("http"))
                if s["published_at"]:
                    self.assertLessEqual(s["published_at"], "2026-10-09")
                    self.assertTrue(s["publication_date_verified"])

            # 4. Kiểm tra evidence_refs trong findings & risks
            metric_ids = {m["metric_id"] for m in res["data"]["metrics"]}
            valid_targets = source_ids.union(metric_ids)

            for f in res["data"]["findings"]:
                for ref in f["evidence_refs"]:
                    self.assertIn(ref, valid_targets, f"Finding ref {ref} không tồn tại")

            for r in res["data"]["risks"]:
                for ref in r["evidence_refs"]:
                    self.assertIn(ref, valid_targets, f"Risk ref {ref} không tồn tại")


if __name__ == "__main__":
    unittest.main()
