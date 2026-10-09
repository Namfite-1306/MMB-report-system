import copy
import json
import math
import sys
import unicodedata
from pathlib import Path

from strategy_v2 import (
    Engine,
    ContractError,
    MissingData,
    check,
    defaults,
    demo_input,
    evaluate,
    numeric,
    read_json,
    write_json,
)


ROOT = Path(__file__).resolve().parent

POLICY = {
    "version": "mvp-1.0",
    "upside_threshold": 0.15,
    "threshold_basis": "Group MVP policy; not a Graham/Dodd standard.",
    "relative_weight": 0.60,
    "graham_weight": 0.40,
    "weight_basis": "Group experimental policy; not empirically validated.",
    "minimum_peers": 3,
    "dcf_role": "optional_reference",
    "financial_risk_policy": (
        "Attractive requires a sourced safe assessment with explicit rationale. "
        "No universal D/E or Altman threshold is assumed."
    ),
}


def rule(rule_id, status, values, explanation, refs=None):
    return {
        "id": rule_id,
        "status": status,
        "values": values,
        "explanation": explanation,
        "evidence_refs": refs or [],
    }


def classify_title(title):
    """Phân loại chủ đề, không suy ra cảm xúc hoặc tính đúng sai."""
    text = unicodedata.normalize("NFD", title.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.replace("đ", "d")

    keywords = {
        "earnings": (
            "ket qua kinh doanh", "loi nhuan", "doanh thu", "bao cao tai chinh"
        ),
        "dividend": ("co tuc", "chia thuong", "phat hanh co phieu"),
        "capacity": ("cong suat", "nha may", "mo rong", "du an moi"),
        "legal": ("phap ly", "khoi to", "xu phat", "kien tung", "thanh tra"),
    }
    return [
        category
        for category, words in keywords.items()
        if any(word in text for word in words)
    ] or ["other"]


def add_keyword_news(engine, output):
    block = engine.payload.get("news")
    if not isinstance(block, dict):
        output["warnings"].append("Chưa có tin tức để phân loại chủ đề.")
        return

    items = block.get("items")
    if not isinstance(items, list):
        output["warnings"].append("Chưa có danh sách tin tức.")
        return

    start = engine.payload["analysis_period"]["start"]
    end = engine.payload["analysis_period"]["end"]
    classified = []
    seen = set()
    engine.used = set()

    for index, item in enumerate(items):
        check(isinstance(item, dict), "Mỗi tin tức phải là object.")
        if item.get("ticker") != engine.payload["ticker"]:
            continue

        path = f"news.items.{index}.title"
        try:
            title = engine.fact(path, "text", "text")
        except MissingData:
            continue

        fact = engine.lookup(path)
        if not start <= fact["published_at"] <= end:
            continue
        if fact["source"] in seen:
            continue
        seen.add(fact["source"])

        classified.append({
            "title": title,
            "categories": classify_title(title),
            "source": fact["source"],
            "published_at": fact["published_at"],
            "requires_content_review": True,
        })

    output["data"]["rules"].append(rule(
        "news_keywords",
        "evaluated",
        {"events": classified},
        "Chỉ phân loại chủ đề; không dùng từ khóa để tự kết luận tốt/xấu.",
        sorted(engine.used),
    ))


def financial_risk(engine):
    """
    Nhận đánh giá có nguồn từ Module Doanh nghiệp.
    Nếu không có đánh giá và lý do, rủi ro là unknown.
    """
    details = {}
    try:
        details["debt_to_equity"] = engine.fact("company.de", "fraction")
    except MissingData:
        details["debt_to_equity"] = None

    try:
        assessment = engine.fact("company.financial_risk", "text", "text")
        basis = engine.fact("company.financial_risk_basis", "text", "text")
    except MissingData:
        return {
            **details,
            "status": "unknown",
            "basis": "Chưa có đánh giá rủi ro tài chính được dẫn nguồn.",
        }

    check(assessment in ("safe", "high", "uncertain"),
          "financial_risk phải là safe, high hoặc uncertain.")

    return {
        **details,
        "status": assessment,
        "basis": basis,
        "limitation": (
            "Đánh giá do module đầu vào cung cấp; cần kiểm chứng "
            "phương pháp và tính phù hợp với ngành."
        ),
    }


def target_price(engine, existing_rules, warnings):
    price = engine.fact("company.price", "VND/share")
    check(price > 0, "Giá thị trường phải dương.")

    eps = engine.fact("company.eps_ttm", "VND/share")
    if eps <= 0:
        raise MissingData(
            "EPS TTM không dương; không áp dụng phương pháp EPS của MVP."
        )

    normalized = engine.fact(
        "company.earnings_normalized", "boolean", "boolean"
    )
    if not normalized:
        raise MissingData("Chưa có EPS phù hợp sau xem xét lợi nhuận bất thường.")

    company = engine.lookup("company")
    business = company.get("business_type")
    check(business in ("nonfinancial", "bank", "securities"),
          "Thiếu business_type phù hợp.")

    method = "PB" if business in ("bank", "securities") else "PE"
    field = "bvps" if method == "PB" else "eps_ttm"
    denominator = engine.fact(f"company.{field}", "VND/share")
    if denominator <= 0:
        raise MissingData(f"{field} không dương.")

    median_path = (
        "industry.ind_pb_median" if method == "PB"
        else "industry.ind_pe_median"
    )

    # Ưu tiên trung vị đã được Module Ngành tính.
    try:
        median = engine.fact(median_path, "multiple")
        check(median > 0, "Trung vị định giá phải dương.")

        peer_count = engine.fact("industry.peer_count", "count")
        check(type(peer_count) is int and peer_count >= 0,
              "peer_count phải là số nguyên không âm.")
        if peer_count < POLICY["minimum_peers"]:
            raise MissingData("Nhóm so sánh chưa đủ số lượng theo chính sách MVP.")

        note = engine.fact("industry.comparability_note", "text", "text")
        engine.compatible(
            [median_path, f"company.{field}"]
        )
        engine.compatible(
            [median_path, "company.price"], same_date=True
        )
        group_sector = engine.lookup("industry").get("sector")
        check(group_sector == engine.payload["sector"],
              "Trung vị ngành không khớp ngành doanh nghiệp.")
        check(
            engine.lookup("industry").get("accounting_basis")
            == company.get("accounting_basis")
            and isinstance(company.get("accounting_basis"), str),
            "Khác hoặc thiếu cơ sở kế toán.",
        )
        relative_source = "industry_supplied_median"
        warnings.append("Cần kiểm chứng nhóm so sánh: " + note)

    except MissingData:
        # Nếu chưa có trung vị trực tiếp, dùng kết quả peer của v2.
        old = existing_rules.get("relative_valuation")
        if not old or not old.get("values"):
            raise MissingData("Thiếu trung vị ngành hoặc nhóm peer tương thích.")
        estimate = old["values"]["estimates"].get(method)
        if not estimate:
            raise MissingData(f"Chưa có định giá tương đối {method}.")
        median = estimate["peer_median"]
        engine.used.update(old["evidence_refs"])
        relative_source = "v2_verified_contract_peers"

    relative_target = denominator * median
    graham_reference = None
    target = relative_target
    target_method = method

    # Graham chỉ bổ sung khi doanh nghiệp và dữ liệu đủ điều kiện.
    if business == "nonfinancial":
        try:
            applicable = engine.fact(
                "company.graham_applicable", "boolean", "boolean"
            )
            if applicable:
                engine.fact("company.graham_basis", "text", "text")
                eps_average = engine.fact("company.eps_avg_3y", "VND/share")
                bvps = engine.fact("company.bvps", "VND/share")
                if eps_average > 0 and bvps > 0:
                    graham_reference = math.sqrt(22.5 * eps_average * bvps)
                    target = (
                        POLICY["relative_weight"] * relative_target
                        + POLICY["graham_weight"] * graham_reference
                    )
                    target_method = "60% PE + 40% Graham screening reference"
                    warnings.append(
                        "Graham Number là mức sàng lọc tham chiếu; "
                        "trọng số 60/40 là chính sách thử nghiệm của nhóm."
                    )
        except MissingData:
            pass

    if graham_reference is None:
        warnings.append(
            "Không đủ điều kiện Graham; dùng định giá tương đối "
            "với trọng số 100%, không tự điền dữ liệu."
        )

    check(numeric(target) and target > 0, "Giá mục tiêu không hợp lệ.")
    return {
        "market_price": price,
        "method": target_method,
        "relative_method": method,
        "median_multiple": median,
        "relative_source": relative_source,
        "relative_target": relative_target,
        "graham_reference": graham_reference,
        "target_price": target,
        "target_price_unit": "VND/share",
        "upside": target / price - 1,
        "margin_of_safety": 1 - price / target,
        "valuation_date": engine.lookup("company.price")["observed_at"],
        "limitation": (
            "Giá mục tiêu là tham chiếu theo phương pháp, không phải "
            "dự báo giá chắc chắn sau thời hạn đầu tư."
        ),
    }


def decide(payload, config):
    working_config = copy.deepcopy(config)

    # DCF/định giá nội tại chỉ là tham chiếu tùy chọn.
    working_config["modules"]["value"]["enabled"] = False

    output = evaluate(payload, working_config)
    if output["status"] == "error":
        return output

    engine = Engine(payload, working_config)

    try:
        engine.validate_sources(payload)
        existing = {r["id"]: r for r in output["data"]["rules"]}
        engine.used = set()

        risk = financial_risk(engine)
        risk_refs = sorted(engine.used)

        target = None
        target_refs = []
        missing_reason = None
        engine.used = set()

        try:
            target = target_price(engine, existing, output["warnings"])
            target_refs = sorted(engine.used)
        except MissingData as exc:
            missing_reason = str(exc)

        if target is None:
            label = "insufficient_data"
            rationale = missing_reason

        elif risk["status"] == "high":
            label = "unattractive"
            rationale = "Có đánh giá rủi ro tài chính cao: " + risk["basis"]

        elif target["upside"] < -1e-12:
            label = "unattractive"
            rationale = "Giá thị trường cao hơn giá tham chiếu theo mô hình."

        elif (
            target["upside"] + 1e-12 >= POLICY["upside_threshold"]
            and risk["status"] == "safe"
        ):
            label = "attractive"
            rationale = (
                "Upside đạt ngưỡng 15% theo chính sách MVP "
                "và đầu vào đánh giá rủi ro tài chính ở mức safe."
            )

        else:
            label = "watchlist"
            if risk["status"] in ("unknown", "uncertain"):
                rationale = (
                    "Đã có giá tham chiếu nhưng chưa xác nhận "
                    "rủi ro tài chính an toàn; cần theo dõi."
                )
            else:
                rationale = "Upside không âm nhưng chưa đạt ngưỡng 15%."

        output["data"]["rules"].append(rule(
            "mvp_target_price",
            "evaluated" if target else "insufficient_data",
            target,
            missing_reason or "Ưu tiên định giá tương đối; Graham là bổ sung.",
            target_refs,
        ))

        conditions = {
            "target_available": target is not None,
            "upside_at_least_15_percent": (
                None if target is None
                else target["upside"] + 1e-12 >= POLICY["upside_threshold"]
            ),
            "financial_risk_safe": (
                None if risk["status"] in ("unknown", "uncertain")
                else risk["status"] == "safe"
            ),
            "financial_risk_high": risk["status"] == "high",
        }

        output["data"]["rules"].append(rule(
            "mvp_decision_matrix",
            "evaluated" if target else "insufficient_data",
            conditions,
            rationale,
            sorted(set(target_refs + risk_refs)),
        ))

        # Giữ thông tin chẩn đoán của v2; không để thiếu CAPM/DCF
        # làm mất giá tham chiếu và kết luận MVP.
        previous_conclusion = output["data"]["conclusion"]
        output["data"]["conclusion"] = {
            "label": label,
            "label_display": {
                "attractive": "MUA THEO CHÍNH SÁCH MVP",
                "watchlist": "THEO DÕI",
                "unattractive": "KHÔNG HẤP DẪN",
                "insufficient_data": "CHƯA ĐỦ DỮ LIỆU",
            }[label],
            "target_price": None if target is None else target["target_price"],
            "target_price_unit": "VND/share",
            "upside": None if target is None else target["upside"],
            "margin_of_safety": (
                None if target is None else target["margin_of_safety"]
            ),
            "rationale": rationale,
            "policy_version": POLICY["version"],
            "is_demo": payload["is_demo"],
            "real_data_verified": False,
            "optional_missing_modules": previous_conclusion["missing_modules"],
            "conflicting_signals": previous_conclusion["conflicting_signals"],
        }
        output["data"]["mvp_policy"] = copy.deepcopy(POLICY)
        output["data"]["risks"]["financial_assessment"] = risk
        output["data"]["risks"]["valuation"] = (
            None if target is None else {
                "method": target["method"],
                "limitation": target["limitation"],
            }
        )

        add_keyword_news(engine, output)

        output["sources"] = list(engine.sources.values())
        output["data"]["evidence_refs"].update(engine.evidence)
        output["warnings"].append(
            "Nhãn được sinh theo chính sách MVP; chưa kiểm chứng "
            "hiệu quả đầu tư bằng dữ liệu thật."
        )
        if payload["is_demo"]:
            output["warnings"].append(
                "Dữ liệu giả lập: không dùng nhãn này để ra quyết định thực tế."
            )
            output["status"] = "demo_only"
        elif target is None:
            output["status"] = "insufficient_data"
        else:
            output["status"] = "requires_review"

        output["warnings"] = list(dict.fromkeys(output["warnings"]))
        return output

    except (ContractError, KeyError, TypeError) as exc:
        output["status"] = "error"
        output["data"] = None
        output["errors"] = [{
            "code": "MVP_CONTRACT_ERROR",
            "message": str(exc),
        }]
        return output


def mvp_demo():
    payload = demo_input()

    def fact(value, unit, period="2026-09-30", observed="2026-10-09"):
        return {
            "value": value,
            "unit": unit,
            "source": "https://example.com/mvp-synthetic-test",
            "period": period,
            "observed_at": observed,
            "published_at": "2026-10-09",
        }

    payload["run_id"] = "mvp-demo-001"
    payload["industry"].update({
        "sector": payload["sector"],
        "accounting_basis": payload["company"]["accounting_basis"],
        "ind_pe_median": fact(11, "multiple"),
        "ind_pb_median": fact(2.2, "multiple"),
        "peer_count": fact(3, "count"),
        "comparability_note": fact(
            "Synthetic matched accounting, earnings periods, growth and risk.",
            "text",
        ),
    })
    payload["company"].update({
        "de": fact(0.3, "fraction"),
        "financial_risk": fact("safe", "text"),
        "financial_risk_basis": fact(
            "Synthetic safe assessment for software testing, not real analysis.",
            "text",
        ),
        "graham_applicable": fact(True, "boolean"),
        "graham_basis": fact(
            "Synthetic asset-based company assumption for software testing.",
            "text",
        ),
        "eps_avg_3y": fact(10, "VND/share", "2024-2026"),
    })
    return payload


def self_test():
    config = defaults()
    payload = mvp_demo()
    output = decide(payload, config)
    assert not output["errors"], output["errors"]

    conclusion = output["data"]["conclusion"]
    expected = 0.6 * (12 * 11) + 0.4 * math.sqrt(22.5 * 10 * 60)
    assert math.isclose(conclusion["target_price"], expected)
    assert conclusion["label"] == "attractive"
    assert output["status"] == "demo_only"

    # Tắt Graham để kiểm tra ranh giới ma trận thuần P/E.
    base = copy.deepcopy(payload)
    base["company"]["graham_applicable"]["value"] = False
    base["company"]["eps_ttm"]["value"] = 10

    for median, risk, expected_label in (
        (11.5, "safe", "attractive"),
        (11.49, "safe", "watchlist"),
        (10, "safe", "watchlist"),
        (9.99, "safe", "unattractive"),
        (15, "high", "unattractive"),
        (15, "uncertain", "watchlist"),
    ):
        case = copy.deepcopy(base)
        case["industry"]["ind_pe_median"]["value"] = median
        case["company"]["financial_risk"]["value"] = risk
        result = decide(case, config)
        assert not result["errors"], result["errors"]
        assert result["data"]["conclusion"]["label"] == expected_label

    case = copy.deepcopy(base)
    case["company"]["eps_ttm"]["value"] = -1
    assert decide(case, config)["data"]["conclusion"]["label"] == "insufficient_data"

    case = copy.deepcopy(base)
    case["company"].pop("financial_risk")
    assert decide(case, config)["data"]["conclusion"]["label"] == "watchlist"

    case = copy.deepcopy(base)
    case["industry"]["ind_pe_median"]["published_at"] = "2026-10-10"
    assert decide(case, config)["status"] == "error"

    assert classify_title("Doanh nghiệp chia cổ tức") == ["dividend"]
    assert "legal" in classify_title("Doanh nghiệp bị xử phạt")
    print("MVP self-test passed.")


if __name__ == "__main__":
    args = sys.argv[1:]

    if args == ["--init"]:
        path = ROOT / "input_mvp_demo.json"
        if path.exists():
            print("Giữ input_mvp_demo.json hiện có.")
        else:
            write_json(path, mvp_demo())
            print("Đã tạo input_mvp_demo.json.")

    elif args == ["--self-test"]:
        self_test()

    elif len(args) == 2:
        payload = None
        try:
            payload = read_json(args[0])
            config = read_json(ROOT / "strategy_rules_v2.json")
            result = decide(payload, config)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            metadata = payload if isinstance(payload, dict) else {}
            result = {
                "schema_version": "1.0",
                "run_id": metadata.get("run_id"),
                "ticker": metadata.get("ticker"),
                "as_of": metadata.get("as_of"),
                "status": "error",
                "data": None,
                "sources": [],
                "warnings": [],
                "errors": [{
                    "code": "INPUT_OR_CONFIG_ERROR",
                    "message": str(exc),
                }],
            }
        write_json(args[1], result)
        print(f"Đã tạo {args[1]}; status={result['status']}")
        raise SystemExit(1 if result["status"] == "error" else 0)

    else:
        raise SystemExit(
            "Dùng: --init | --self-test | INPUT.json OUTPUT.json"
        )