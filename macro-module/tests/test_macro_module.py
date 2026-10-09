"""Kiểm tra hợp đồng dữ liệu cho Module 1 - Vĩ mô."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from macro_module import build_macro_result, load_json, write_json  # noqa: E402


class MacroModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = load_json(ROOT / "examples" / "input.sample.json")
        cls.dataset = load_json(ROOT / "data" / "verified_macro_data.json")
        cls.mapping = load_json(ROOT / "config" / "industry_mapping.json")

    def build(self, payload=None, dataset=None):
        return build_macro_result(
            payload or copy.deepcopy(self.payload),
            dataset or copy.deepcopy(self.dataset),
            copy.deepcopy(self.mapping),
        )

    def test_contract_and_input_passthrough(self):
        result = self.build()
        for field in ("schema_version", "run_id", "ticker", "as_of_date"):
            self.assertEqual(result[field], self.payload[field])
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["data"]["metadata"]["input"]["exchange"], "HOSE")
        self.assertEqual(result["data"]["metadata"]["input"]["industry"], "Công nghệ thông tin")
        self.assertIsInstance(result["sources"], list)
        self.assertIsInstance(result["warnings"], list)
        self.assertIsInstance(result["errors"], list)
        json.dumps(result, ensure_ascii=False, allow_nan=False)

    def test_exchange_rate_is_integer_24337_vnd_per_usd(self):
        result = self.build()
        indicator = next(item for item in result["data"]["indicators"] if item["group"] == "exchange_rate")
        self.assertEqual(indicator["value"], 24337)
        self.assertIsInstance(indicator["value"], int)
        self.assertEqual(indicator["unit"], "VND/USD")
        self.assertIn("phân cách hàng nghìn", indicator["value_note"])

    def test_publication_effective_and_access_dates_are_distinct(self):
        result = self.build()
        rate = next(item for item in result["data"]["indicators"] if item["group"] == "policy_rate")
        source = next(item for item in result["sources"] if item["source_id"] == rate["source_id"])
        self.assertEqual(rate["publication_date"], "2023-06-16")
        self.assertEqual(rate["effective_date"], "2023-06-19")
        self.assertEqual(source["access_date"], "2026-10-09")
        self.assertNotEqual(rate["publication_date"], rate["effective_date"])
        self.assertNotEqual(rate["effective_date"], source["access_date"])

    def test_partial_status_has_explicit_quality_reason_not_missing_value(self):
        result = self.build()
        self.assertEqual(result["status"], "partial")
        reasons = result["data"]["metadata"]["status_details"]["reason_codes"]
        self.assertEqual(reasons, ["SOURCE_QUALITY_POLICY"])
        warning = next(item for item in result["warnings"] if item["code"] == "SOURCE_QUALITY_POLICY")
        self.assertEqual(warning["category"], "source_quality")
        self.assertTrue(warning["affects_status"])
        self.assertIn("không phải vì thiếu giá trị số", warning["message"])
        self.assertFalse(any(item["code"].startswith("MISSING_") for item in result["warnings"]))

    def test_secondary_source_does_not_automatically_force_partial(self):
        dataset = copy.deepcopy(self.dataset)
        fx_source = next(item for item in dataset["sources"] if item["classification"] == "secondary")
        fx_source["quality_treatment"] = "accepted_secondary"
        result = self.build(dataset=dataset)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["metadata"]["status_details"]["reason_codes"], [])

    def test_required_indicator_groups_and_units(self):
        result = self.build()
        indicators = {item["group"]: item for item in result["data"]["indicators"]}
        self.assertEqual(set(indicators), {"gdp", "cpi", "policy_rate", "exchange_rate"})
        self.assertEqual(indicators["gdp"]["value"], 0.0709)
        self.assertEqual(indicators["cpi"]["value"], 0.0363)
        self.assertEqual(indicators["policy_rate"]["name"], "Lãi suất tái cấp vốn của Ngân hàng Nhà nước")

    def test_no_source_published_after_cutoff(self):
        result = self.build()
        cutoff = date.fromisoformat(result["as_of_date"])
        for source in result["sources"]:
            self.assertLessEqual(date.fromisoformat(source["publication_date"]), cutoff)

    def test_snapshot_refresh_metadata_is_explicit(self):
        result = self.build()
        dataset = result["data"]["metadata"]["dataset"]
        self.assertEqual(dataset["verified_through"], "2025-01-06")
        self.assertEqual(dataset["snapshot_kind"], "static_verified_snapshot")
        self.assertEqual(dataset["refresh_behavior"], "local_snapshot_only_no_network_fetch")
        self.assertFalse(dataset["network_fetch_performed"])

    def test_missing_data_returns_full_structure(self):
        empty_dataset = {
            "dataset_id": "empty",
            "dataset_version": "1",
            "collection_method": "verified_local_file",
            "observations": [],
            "sources": [],
        }
        result = self.build(dataset=empty_dataset)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(len(result["data"]["indicators"]), 4)
        self.assertTrue(all(item["value"] is None for item in result["data"]["indicators"]))
        self.assertGreaterEqual(len(result["warnings"]), 4)
        self.assertTrue(all(item["category"] == "missing_data" for item in result["warnings"]))
        self.assertEqual(result["errors"], [])

    def test_unknown_industry_does_not_crash(self):
        payload = copy.deepcopy(self.payload)
        payload["industry"] = "Ngành thử nghiệm chưa ánh xạ"
        result = self.build(payload=payload)
        self.assertEqual(result["status"], "partial")
        self.assertTrue(any(item["code"] == "UNMAPPED_INDUSTRY" for item in result["warnings"]))
        self.assertEqual(result["data"]["metadata"]["industry_mapping"]["input_preserved"], payload["industry"])

    def test_same_cutoff_reuses_macro_context_but_changes_industry_impacts(self):
        tech = self.build()
        bank_input = copy.deepcopy(self.payload)
        bank_input.update({"ticker": "VCB", "industry": "Ngân hàng"})
        bank = self.build(payload=bank_input)
        self.assertEqual(tech["data"]["metadata"]["dataset"]["cache_key"], bank["data"]["metadata"]["dataset"]["cache_key"])
        self.assertEqual(tech["data"]["indicators"], bank["data"]["indicators"])
        self.assertNotEqual(tech["data"]["industry_impacts"], bank["data"]["industry_impacts"])

    def test_cutoff_after_verified_range_is_partial(self):
        payload = copy.deepcopy(self.payload)
        payload["as_of_date"] = "2025-02-01"
        payload["analysis_period"]["end_date"] = "2025-02-01"
        result = self.build(payload=payload)
        self.assertEqual(result["status"], "partial")
        self.assertTrue(any(item["code"] == "DATASET_NOT_VERIFIED_THROUGH_CUTOFF" for item in result["warnings"]))

    def test_writer_refuses_implicit_overwrite(self):
        result = self.build()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "macro.json"
            write_json(result, output)
            with self.assertRaises(FileExistsError):
                write_json(result, output)


if __name__ == "__main__":
    unittest.main()
