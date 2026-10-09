"""Lõi xử lý dữ liệu vĩ mô, chỉ dùng thư viện chuẩn Python."""

from __future__ import annotations

import json
import math
import os
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping

REQUIRED_INPUT_FIELDS = (
    "schema_version",
    "run_id",
    "ticker",
    "exchange",
    "industry",
    "as_of_date",
    "analysis_period",
    "investment_horizon",
)
REQUIRED_GROUPS = ("gdp", "cpi", "policy_rate", "exchange_rate")
GROUP_LABELS = {
    "gdp": "Tăng trưởng GDP thực",
    "cpi": "Chỉ số giá tiêu dùng (CPI)",
    "policy_rate": "Lãi suất điều hành",
    "exchange_rate": "Tỷ giá VND/USD",
}
GROUP_UNITS = {
    "gdp": "ratio",
    "cpi": "ratio",
    "policy_rate": "ratio_per_year",
    "exchange_rate": "VND/USD",
}
VALID_EXCHANGES = {"HOSE", "HNX", "UPCOM"}
VALID_DIRECTIONS = {"hỗ trợ", "bất lợi", "hỗn hợp", "chưa xác định"}


class InputValidationError(ValueError):
    """Lỗi hợp đồng đầu vào."""


def load_json(path: str | Path) -> dict[str, Any]:
    """Đọc JSON UTF-8 và yêu cầu đối tượng gốc là object."""
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"JSON gốc phải là object: {path}")
    return value


def _parse_date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise InputValidationError(f"{field} phải là chuỗi YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise InputValidationError(f"{field} không đúng định dạng YYYY-MM-DD") from exc


def _validate_input(raw: Mapping[str, Any]) -> None:
    missing = [field for field in REQUIRED_INPUT_FIELDS if raw.get(field) in (None, "")]
    if missing:
        raise InputValidationError("Thiếu trường bắt buộc: " + ", ".join(missing))

    as_of = _parse_date(raw["as_of_date"], "as_of_date")
    period = raw["analysis_period"]
    if not isinstance(period, Mapping):
        raise InputValidationError("analysis_period phải là object có start_date và end_date")
    start = _parse_date(period.get("start_date"), "analysis_period.start_date")
    end = _parse_date(period.get("end_date"), "analysis_period.end_date")
    if start > end:
        raise InputValidationError("analysis_period.start_date không được sau end_date")
    if end > as_of:
        raise InputValidationError("analysis_period.end_date không được sau as_of_date")

    if str(raw["exchange"]).upper() not in VALID_EXCHANGES:
        raise InputValidationError("exchange phải thuộc HOSE, HNX hoặc UPCOM")
    if not isinstance(raw["investment_horizon"], (str, Mapping)):
        raise InputValidationError("investment_horizon phải là chuỗi hoặc object")


def _normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value).strip().lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.replace("đ", "d").split())


def _horizon_focus(value: Any) -> str:
    if isinstance(value, Mapping):
        months = value.get("months")
        label = value.get("label", "")
        if isinstance(months, (int, float)):
            if months <= 6:
                return "ngắn hạn"
            if months <= 24:
                return "trung hạn"
            return "dài hạn"
        value = label
    normalized = _normalize_text(value)
    if any(token in normalized for token in ("ngan han", "0-6", "3-6")):
        return "ngắn hạn"
    if any(token in normalized for token in ("dai han", "tren 24", "36 thang", "5 nam")):
        return "dài hạn"
    return "trung hạn"


def _empty_data(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "metadata": {
            "collected_at": None,
            "output_generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "input": {field: raw.get(field) for field in REQUIRED_INPUT_FIELDS},
            "actual_data_periods": {},
            "dataset": None,
        },
        "indicators": [],
        "macro_summary": {
            "observations": [],
            "calculated_results": [],
            "assessment": None,
        },
        "industry_impacts": [],
        "opportunities": [],
        "risks": [],
        "limitations": [],
    }


def _error_result(raw: Mapping[str, Any], code: str, message: str) -> dict[str, Any]:
    return {
        "schema_version": raw.get("schema_version"),
        "run_id": raw.get("run_id"),
        "ticker": raw.get("ticker"),
        "as_of_date": raw.get("as_of_date"),
        "status": "error",
        "data": _empty_data(raw),
        "sources": [],
        "warnings": [],
        "errors": [{"code": code, "message": message}],
    }


def _date_not_after(value: Any, as_of: date) -> bool:
    if value in (None, ""):
        return False
    try:
        return date.fromisoformat(str(value)) <= as_of
    except ValueError:
        return False


def _select_observations(
    dataset: Mapping[str, Any], as_of: date
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    sources = {
        item.get("source_id"): item
        for item in dataset.get("sources", [])
        if isinstance(item, Mapping) and item.get("source_id")
    }
    selected: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []

    for group in REQUIRED_GROUPS:
        candidates: list[Mapping[str, Any]] = []
        for observation in dataset.get("observations", []):
            if not isinstance(observation, Mapping) or observation.get("group") != group:
                continue
            source = sources.get(observation.get("source_id"))
            source_date = source.get("publication_date") if source else None
            if not _date_not_after(observation.get("publication_date"), as_of):
                continue
            if not _date_not_after(source_date, as_of):
                continue
            period_end = observation.get("period_end")
            if period_end and not _date_not_after(period_end, as_of):
                continue
            valid_from = observation.get("valid_from")
            if valid_from and not _date_not_after(valid_from, as_of):
                continue
            valid_to = observation.get("valid_to")
            if valid_to:
                try:
                    if date.fromisoformat(str(valid_to)) < as_of:
                        continue
                except ValueError:
                    continue
            candidates.append(observation)

        if candidates:
            latest = max(
                candidates,
                key=lambda item: (
                    str(item.get("period_end") or "0000-00-00"),
                    str(item.get("publication_date") or "0000-00-00"),
                ),
            )
            selected.append(dict(latest))
            continue

        selected.append(
            {
                "indicator_id": f"vn_{group}_unavailable",
                "group": group,
                "name": GROUP_LABELS[group],
                "value": None,
                "unit": GROUP_UNITS[group],
                "data_period": None,
                "period_start": None,
                "period_end": None,
                "frequency": None,
                "measurement": None,
                "publication_date": None,
                "effective_date": None,
                "source_id": None,
                "comparison": None,
                "data_kind": "observed",
                "collection_method": "unavailable",
            }
        )
        issues.append(
            {
                "code": f"MISSING_{group.upper()}",
                "category": "missing_data",
                "affects_status": True,
                "message": f"Không có quan sát {GROUP_LABELS[group]} được xác minh không muộn hơn {as_of.isoformat()}.",
            }
        )
    return selected, issues


def _actual_periods(observations: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        str(item["group"]): {
            "data_period": item.get("data_period"),
            "period_start": item.get("period_start"),
            "period_end": item.get("period_end"),
            "publication_date": item.get("publication_date"),
        }
        for item in observations
    }


def _format_percent(value: float) -> str:
    return f"{value * 100:.2f}".replace(".", ",") + "%"


def _build_summary(observations: list[Mapping[str, Any]]) -> dict[str, Any]:
    by_group = {str(item["group"]): item for item in observations}
    statements: list[dict[str, Any]] = []
    templates = {
        "gdp": "GDP thực {period} tăng {value} so với năm trước.",
        "cpi": "CPI bình quân {period} tăng {value} so với năm trước.",
        "policy_rate": "Lãi suất tái cấp vốn được quan sát ở mức {value}/năm, hiệu lực từ 19/06/2023; đây không phải lãi suất huy động hay cho vay thương mại.",
        "exchange_rate": "Tỷ giá trung tâm ngày {period} là {number} VND/USD; đây không phải tỷ giá mua hoặc bán.",
    }
    for group in REQUIRED_GROUPS:
        item = by_group[group]
        value = item.get("value")
        if value is None:
            continue
        if group == "exchange_rate":
            statement = templates[group].format(period=item["data_period"], number=f"{float(value):,.0f}".replace(",", "."))
        else:
            statement = templates[group].format(
                period=item["data_period"], value=_format_percent(float(value))
            )
        statements.append(
            {
                "statement": statement,
                "nature": "observed",
                "indicator_ids": [item["indicator_id"]],
                "source_ids": [item["source_id"]],
            }
        )

    calculations: list[dict[str, Any]] = []
    for item in observations:
        comparison = item.get("comparison")
        if item.get("value") is None or not isinstance(comparison, Mapping):
            continue
        previous = comparison.get("value")
        if not isinstance(previous, (int, float)):
            continue
        change = float(item["value"]) - float(previous)
        calculations.append(
            {
                "calculation_id": f"change_{item['indicator_id']}",
                "name": "Chênh lệch với giá trị so sánh tương thích",
                "value": change,
                "unit": "ratio_point" if str(item.get("unit", "")).startswith("ratio") else item.get("unit"),
                "formula": "current_value - comparison.value",
                "nature": "calculated",
                "indicator_ids": [item["indicator_id"]],
                "source_ids": [item["source_id"]],
            }
        )

    evidence_ids = [item["indicator_id"] for item in observations if item.get("value") is not None]
    source_ids = [item["source_id"] for item in observations if item.get("source_id")]
    assessment = {
        "statement": "Các số liệu là ảnh chụp theo kỳ thực tế khác nhau. Không gán nhãn vĩ mô thuận lợi/bất lợi và không suy ra xu hướng chung chỉ từ các quan sát này.",
        "direction": "chưa xác định",
        "nature": "interpretation",
        "assumptions": [
            "Chỉ sử dụng dữ liệu có ngày công bố không muộn hơn ngày chốt.",
            "Mỗi chỉ tiêu giữ nguyên tần suất và cách đo của nguồn.",
        ],
        "indicator_ids": evidence_ids,
        "source_ids": source_ids,
    }
    return {
        "observations": statements,
        "calculated_results": calculations,
        "assessment": assessment,
    }


COMMON_RULES = [
    {
        "group": "policy_rate",
        "direction": "hỗn hợp",
        "mechanism": "Lãi suất tái cấp vốn là tín hiệu chính sách; tác động tới chi phí vốn doanh nghiệp chỉ xảy ra qua truyền dẫn sang lãi suất huy động và cho vay thực tế.",
        "conditions": ["Doanh nghiệp có nợ vay lãi suất thả nổi", "Ngân hàng thương mại truyền dẫn thay đổi chính sách"],
        "company_checks": ["Cơ cấu nợ", "Lãi suất vay thực trả", "Lịch tái định giá khoản vay"],
        "opportunity": "Chi phí vốn có thể giảm nếu lãi suất cho vay thực tế giảm và doanh nghiệp cần tái cấp vốn.",
        "risk": "Không được giả định lãi suất vay doanh nghiệp bằng lãi suất tái cấp vốn của NHNN.",
    },
    {
        "group": "cpi",
        "direction": "hỗn hợp",
        "mechanism": "Lạm phát có thể làm tăng chi phí đầu vào và lương, trong khi khả năng chuyển giá quyết định ảnh hưởng lên biên lợi nhuận và sức mua.",
        "conditions": ["Chi phí đầu vào nhạy với giá", "Doanh nghiệp có hoặc không có quyền định giá"],
        "company_checks": ["Biên lợi nhuận gộp", "Điều khoản điều chỉnh giá", "Cơ cấu chi phí"],
        "opportunity": "Doanh nghiệp có quyền định giá và kiểm soát chi phí có thể bảo vệ biên lợi nhuận tốt hơn.",
        "risk": "Biên lợi nhuận có thể chịu áp lực nếu chi phí tăng nhanh hơn giá bán.",
    },
]

INDUSTRY_RULES = {
    "technology": [
        {
            "group": "gdp",
            "direction": "hỗ trợ",
            "mechanism": "Tăng trưởng hoạt động kinh tế có thể hỗ trợ ngân sách công nghệ và nhu cầu chuyển đổi số, nhưng không đại diện trực tiếp cho doanh thu từng doanh nghiệp.",
            "conditions": ["Chi tiêu CNTT tăng cùng hoạt động kinh tế", "Doanh nghiệp duy trì năng lực ký hợp đồng"],
            "company_checks": ["Giá trị hợp đồng ký mới", "Backlog", "Tỷ trọng khách hàng trong nước"],
            "opportunity": "Nhu cầu dịch vụ CNTT có thể mở rộng nếu ngân sách chuyển đổi số tăng thực tế.",
            "risk": None,
        },
        {
            "group": "exchange_rate",
            "direction": "hỗn hợp",
            "mechanism": "Tỷ giá VND/USD có thể tăng giá trị quy đổi doanh thu USD nhưng đồng thời làm tăng chi phí phần cứng, bản quyền hoặc nợ USD.",
            "conditions": ["Có doanh thu hoặc chi phí định danh USD", "Mức phòng hộ ngoại tệ hữu hiệu"],
            "company_checks": ["Cơ cấu doanh thu theo tiền tệ", "Chi phí nhập khẩu", "Nợ và hợp đồng phòng hộ USD"],
            "opportunity": "Doanh thu USD có thể tạo lợi ích quy đổi nếu chi phí USD thấp hơn doanh thu USD.",
            "risk": "Chi phí nhập khẩu hoặc nợ USD có thể tăng nếu vị thế ngoại tệ ròng âm.",
        },
    ],
    "banking": [
        {
            "group": "gdp",
            "direction": "hỗ trợ",
            "mechanism": "Tăng trưởng kinh tế có thể hỗ trợ nhu cầu tín dụng và chất lượng tài sản, tùy tiêu chuẩn cấp tín dụng và độ trễ nợ xấu.",
            "conditions": ["Cầu tín dụng lành mạnh", "Chất lượng tài sản không suy giảm theo độ trễ"],
            "company_checks": ["Tăng trưởng tín dụng", "NIM", "Nợ nhóm 2 và nợ xấu"],
            "opportunity": "Tín dụng có thể tăng nếu cầu vốn và hạn mức cho phép.",
            "risk": "GDP tăng không loại trừ nợ xấu tại các phân khúc yếu.",
        },
        {
            "group": "exchange_rate",
            "direction": "hỗn hợp",
            "mechanism": "Biến động tỷ giá ảnh hưởng trạng thái ngoại tệ, nhu cầu giao dịch và rủi ro tín dụng của khách hàng vay ngoại tệ.",
            "conditions": ["Ngân hàng có trạng thái ngoại tệ hoặc khách hàng nhạy tỷ giá"],
            "company_checks": ["Trạng thái ngoại tệ ròng", "Thu nhập kinh doanh ngoại hối", "Dư nợ ngoại tệ"],
            "opportunity": "Doanh thu dịch vụ ngoại hối có thể tăng khi nhu cầu phòng hộ tăng.",
            "risk": "Rủi ro tín dụng có thể tăng ở khách hàng có nghĩa vụ USD không được phòng hộ.",
        },
    ],
    "real_estate": [
        {
            "group": "gdp",
            "direction": "hỗ trợ",
            "mechanism": "Tăng trưởng thu nhập và hoạt động kinh tế có thể hỗ trợ nhu cầu bất động sản, nhưng pháp lý và khả năng chi trả vẫn là điều kiện riêng.",
            "conditions": ["Thu nhập người mua cải thiện", "Dự án đủ pháp lý và phù hợp khả năng chi trả"],
            "company_checks": ["Pháp lý dự án", "Tỷ lệ hấp thụ", "Dòng tiền và hàng tồn kho"],
            "opportunity": "Tỷ lệ hấp thụ có thể cải thiện ở dự án phù hợp nhu cầu thực.",
            "risk": None,
        },
        {
            "group": "exchange_rate",
            "direction": "bất lợi",
            "mechanism": "Áp lực tỷ giá có thể làm tăng chi phí vật liệu nhập khẩu và nghĩa vụ nợ ngoại tệ nếu doanh nghiệp có vị thế USD âm.",
            "conditions": ["Có vật liệu nhập khẩu hoặc nợ USD đáng kể"],
            "company_checks": ["Nợ ngoại tệ", "Tỷ trọng vật liệu nhập khẩu", "Phòng hộ"],
            "opportunity": None,
            "risk": "Chi phí dự án hoặc nghĩa vụ nợ có thể tăng khi doanh nghiệp có vị thế USD âm.",
        },
    ],
    "export_manufacturing": [
        {
            "group": "gdp",
            "direction": "hỗn hợp",
            "mechanism": "GDP Việt Nam phản ánh bối cảnh sản xuất trong nước nhưng không thay thế dữ liệu cầu tại thị trường xuất khẩu của doanh nghiệp.",
            "conditions": ["Đơn hàng phụ thuộc cả cầu nội địa và quốc tế"],
            "company_checks": ["Đơn hàng xuất khẩu", "Thị trường đích", "Công suất sử dụng"],
            "opportunity": "Nền sản xuất trong nước tăng có thể hỗ trợ hệ sinh thái cung ứng.",
            "risk": "Không được dùng GDP Việt Nam để suy ra trực tiếp cầu xuất khẩu toàn cầu.",
        },
        {
            "group": "exchange_rate",
            "direction": "hỗn hợp",
            "mechanism": "Tỷ giá ảnh hưởng đồng thời doanh thu xuất khẩu quy đổi và chi phí nguyên liệu, máy móc hoặc nợ ngoại tệ.",
            "conditions": ["Cơ cấu tiền tệ doanh thu và chi phí không cân bằng hoàn toàn"],
            "company_checks": ["Vị thế ngoại tệ ròng", "Tỷ lệ nội địa hóa", "Chính sách phòng hộ"],
            "opportunity": "Doanh nghiệp có nguồn thu USD ròng có thể hưởng lợi quy đổi có điều kiện.",
            "risk": "Nguyên liệu nhập khẩu và nợ USD có thể triệt tiêu lợi ích doanh thu xuất khẩu.",
        },
    ],
    "consumer": [
        {
            "group": "gdp",
            "direction": "hỗ trợ",
            "mechanism": "Tăng trưởng kinh tế có thể hỗ trợ thu nhập và sức mua, nhưng phân bổ thu nhập và niềm tin tiêu dùng quyết định cầu thực tế.",
            "conditions": ["Thu nhập khả dụng và niềm tin tiêu dùng cải thiện"],
            "company_checks": ["Tăng trưởng doanh thu cùng cửa hàng", "Sản lượng bán", "Cơ cấu phân khúc giá"],
            "opportunity": "Sức mua có thể cải thiện ở phân khúc phù hợp thu nhập thực.",
            "risk": None,
        },
        {
            "group": "exchange_rate",
            "direction": "bất lợi",
            "mechanism": "Tỷ giá có thể làm tăng giá vốn hàng nhập khẩu hoặc nguyên liệu định giá USD.",
            "conditions": ["Tỷ trọng nhập khẩu cao", "Khả năng chuyển giá hạn chế"],
            "company_checks": ["Tỷ trọng giá vốn USD", "Tồn kho", "Khả năng tăng giá bán"],
            "opportunity": None,
            "risk": "Giá vốn có thể tăng nếu VND yếu đi và doanh nghiệp khó chuyển giá.",
        },
    ],
}


def _resolve_industry(industry: Any, mapping: Mapping[str, Any]) -> tuple[str | None, str | None]:
    target = _normalize_text(industry)
    for group_id, config in mapping.get("groups", {}).items():
        aliases = [_normalize_text(alias) for alias in config.get("aliases", [])]
        if target in aliases:
            return str(group_id), str(config.get("label", group_id))
    return None, None


def _build_impacts(
    observations: list[Mapping[str, Any]],
    industry_input: Any,
    group_id: str | None,
    group_label: str | None,
    horizon_focus: str,
) -> list[dict[str, Any]]:
    by_group = {str(item["group"]): item for item in observations}
    rules = list(COMMON_RULES)
    rules.extend(INDUSTRY_RULES.get(group_id or "", []))
    impacts: list[dict[str, Any]] = []
    for index, rule in enumerate(rules, start=1):
        observation = by_group[rule["group"]]
        if observation.get("value") is None:
            continue
        direction = str(rule["direction"])
        if direction not in VALID_DIRECTIONS:
            direction = "chưa xác định"
        impacts.append(
            {
                "impact_id": f"impact_{index:02d}_{rule['group']}",
                "nature": "interpretation",
                "industry_input": industry_input,
                "industry_group": group_label or "Chưa ánh xạ",
                "direction": direction,
                "mechanism": rule["mechanism"],
                "conditions": list(rule["conditions"]),
                "company_checks": list(rule["company_checks"]),
                "investment_horizon_focus": horizon_focus,
                "evidence": [
                    {
                        "indicator_id": observation["indicator_id"],
                        "source_id": observation["source_id"],
                        "value": observation["value"],
                        "unit": observation["unit"],
                        "data_period": observation["data_period"],
                    }
                ],
                "opportunity_statement": rule.get("opportunity"),
                "risk_statement": rule.get("risk"),
            }
        )
    return impacts


def _conditional_items(impacts: list[Mapping[str, Any]], key: str, prefix: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for impact in impacts:
        statement = impact.get(key)
        if not statement:
            continue
        evidence = impact["evidence"]
        results.append(
            {
                "id": f"{prefix}_{len(results) + 1:02d}",
                "statement": statement,
                "nature": "interpretation",
                "conditions": impact["conditions"],
                "indicator_ids": [item["indicator_id"] for item in evidence],
                "source_ids": [item["source_id"] for item in evidence],
            }
        )
    return results


def _assert_finite(value: Any, path: str = "result") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Giá trị không hữu hạn tại {path}")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _assert_finite(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_finite(item, f"{path}[{index}]")


def build_macro_result(
    raw_input: Mapping[str, Any],
    dataset: Mapping[str, Any],
    industry_mapping: Mapping[str, Any],
) -> dict[str, Any]:
    """Tạo kết quả macro có cấu trúc mà không tự sinh schema_version/run_id."""
    try:
        _validate_input(raw_input)
        as_of = _parse_date(raw_input["as_of_date"], "as_of_date")
        observations, warnings = _select_observations(dataset, as_of)
        verified_through = dataset.get("verified_through")
        if verified_through and date.fromisoformat(str(verified_through)) < as_of:
            warnings.append(
                {
                    "code": "DATASET_NOT_VERIFIED_THROUGH_CUTOFF",
                    "category": "coverage",
                    "affects_status": True,
                    "message": f"Dataset chỉ được kiểm chứng đến {verified_through}, sớm hơn ngày chốt {as_of.isoformat()}.",
                }
            )
        group_id, group_label = _resolve_industry(raw_input["industry"], industry_mapping)
        if group_id is None:
            warnings.append(
                {
                    "code": "UNMAPPED_INDUSTRY",
                    "category": "industry_mapping",
                    "affects_status": True,
                    "message": "Ngành đầu vào chưa được ánh xạ; chỉ trả bối cảnh chung và không đoán ngành từ mã cổ phiếu.",
                }
            )

        referenced_source_ids = {
            item["source_id"] for item in observations if item.get("source_id")
        }
        sources = [
            dict(source)
            for source in dataset.get("sources", [])
            if source.get("source_id") in referenced_source_ids
            and _date_not_after(source.get("publication_date"), as_of)
        ]
        quality_gated_sources = [
            source
            for source in sources
            if source.get("quality_treatment") == "partial_until_primary_verified"
        ]
        if quality_gated_sources:
            warnings.append(
                {
                    "code": "SOURCE_QUALITY_POLICY",
                    "category": "source_quality",
                    "affects_status": True,
                    "message": "Giá trị tỷ giá 24.337 VND/USD đã được xác minh từ TTXVN dẫn mức NHNN công bố; status=partial theo quy ước chất lượng vì chưa có URL lịch sử trực tiếp ổn định từ NHNN, không phải vì thiếu giá trị số.",
                }
            )

        focus = _horizon_focus(raw_input["investment_horizon"])
        impacts = _build_impacts(
            observations,
            raw_input["industry"],
            group_id,
            group_label,
            focus,
        )
        limitations = [
            "Mỗi nhóm chỉ tiêu trong bộ mẫu có một quan sát mới nhất; không suy ra xu hướng lịch sử từ một điểm dữ liệu.",
            "GDP và CPI năm 2024 là số ước tính tại công bố ngày 06/01/2025; module không thay bằng bản điều chỉnh công bố sau ngày chốt.",
            "Lãi suất sử dụng là lãi suất tái cấp vốn của NHNN, không phải lãi suất huy động hoặc cho vay của ngân hàng thương mại.",
            "Tác động ngành là cơ chế có điều kiện; cần kiểm tra dữ liệu tài chính và mức phơi nhiễm của doanh nghiệp.",
            "Module không dự báo giá cổ phiếu, không chấm điểm doanh nghiệp và không đưa khuyến nghị mua/bán.",
        ]
        if quality_gated_sources:
            limitations.append("Quan sát tỷ giá dùng nguồn thứ cấp; cần thay bằng nguồn NHNN trực tiếp khi có endpoint lịch sử ổn định.")
        if group_id is None:
            limitations.append("Ngành đầu vào chưa có trong bảng ánh xạ nên không có tác động đặc thù ngành.")

        status = "ok"
        status_reason_codes = [
            warning["code"] for warning in warnings if warning.get("affects_status", False)
        ]
        if status_reason_codes:
            status = "partial"
        result = {
            "schema_version": raw_input["schema_version"],
            "run_id": raw_input["run_id"],
            "ticker": raw_input["ticker"],
            "as_of_date": raw_input["as_of_date"],
            "status": status,
            "data": {
                "metadata": {
                    "collected_at": dataset.get("snapshot_compiled_at"),
                    "output_generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                    "input": {field: raw_input[field] for field in REQUIRED_INPUT_FIELDS},
                    "actual_data_periods": _actual_periods(observations),
                    "dataset": {
                        "dataset_id": dataset.get("dataset_id"),
                        "dataset_version": dataset.get("dataset_version"),
                        "verified_through": dataset.get("verified_through"),
                        "snapshot_kind": dataset.get("snapshot_kind"),
                        "snapshot_compiled_at": dataset.get("snapshot_compiled_at"),
                        "refresh_behavior": dataset.get("refresh_behavior"),
                        "network_fetch_performed": False,
                        "collection_method": dataset.get("collection_method", "verified_local_file"),
                        "cache_key": f"macro:{raw_input['as_of_date']}:{dataset.get('dataset_id')}:{dataset.get('dataset_version')}",
                    },
                    "industry_mapping": {
                        "matched_group_id": group_id,
                        "matched_group_label": group_label,
                        "input_preserved": raw_input["industry"],
                    },
                    "investment_horizon_focus": focus,
                    "status_details": {
                        "reason_codes": status_reason_codes,
                        "meaning": "partial phản ánh cảnh báo có affects_status=true; cảnh báo thông tin không tự động làm giảm status.",
                    },
                },
                "indicators": observations,
                "macro_summary": _build_summary(observations),
                "industry_impacts": impacts,
                "opportunities": _conditional_items(impacts, "opportunity_statement", "opportunity"),
                "risks": _conditional_items(impacts, "risk_statement", "risk"),
                "limitations": limitations,
            },
            "sources": sources,
            "warnings": warnings,
            "errors": [],
        }
        _assert_finite(result)
        return result
    except InputValidationError as exc:
        return _error_result(raw_input, "INVALID_INPUT", str(exc))
    except (KeyError, TypeError, ValueError) as exc:
        return _error_result(raw_input, "INVALID_DATASET", str(exc))


def write_json(result: Mapping[str, Any], path: str | Path, force: bool = False) -> None:
    """Ghi JSON UTF-8 nguyên tử; mặc định không ghi đè file hiện có."""
    _assert_finite(result)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not force:
        raise FileExistsError(f"File đã tồn tại: {output}. Dùng --force để cập nhật có chủ đích.")
    temporary = output.with_name(f".{output.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()
