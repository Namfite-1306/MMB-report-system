"""Contract schema validator and enforcement for Người 2 (Module Ngành).
Tuân thủ 100% hợp đồng dữ liệu chung V1 quy định trong Đề án:
- JSON UTF-8
- schema_version = '1.0'
- module = 'industry'
- Tiền tệ: VND
- Tỷ lệ: dạng thập phân (0.12 = 12%), tuyệt đối không dùng ký tự %
- Ngày: YYYY-MM-DD
- Dữ liệu thiếu: null, không thay bằng 0
- Nguồn: source_id duy nhất có prefix 'ind_src_', URL, published_at, publication_date_verified
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Any, Dict, List, Optional, Tuple


DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ContractValidationError(Exception):
    """Lỗi vi phạm hợp đồng dữ liệu Input/Output V1."""
    pass


def validate_date(date_str: Optional[str], field_name: str) -> None:
    if date_str is None:
        return
    if not isinstance(date_str, str) or not DATE_REGEX.match(date_str):
        raise ContractValidationError(f"Trường '{field_name}' phải là chuỗi ngày YYYY-MM-DD, nhận: {date_str!r}")
    try:
        dt.date.fromisoformat(date_str)
    except ValueError as e:
        raise ContractValidationError(f"Trường '{field_name}' có ngày không hợp lệ: {date_str!r}") from e


def validate_number_not_percent(val: Any, field_name: str) -> None:
    if val is None:
        return
    if isinstance(val, str):
        if "%" in val:
            raise ContractValidationError(
                f"Trường '{field_name}' vi phạm quy ước: tỷ lệ phải là số thập phân (ví dụ 0.12 thay vì '12%'). Nhận: {val!r}"
            )
        try:
            val = float(val)
        except ValueError:
            raise ContractValidationError(f"Trường '{field_name}' phải là số (number) hoặc null, nhận: {val!r}")
    elif not isinstance(val, (int, float)):
        raise ContractValidationError(f"Trường '{field_name}' phải là số (number) hoặc null, nhận kiểu {type(val).__name__}")


def validate_industry_output(doc: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Kiểm tra toàn diện tính hợp lệ của output industry.json theo hợp đồng V1.
    
    Returns:
        (is_valid: bool, errors: List[str])
    """
    errors: List[str] = []

    # 1. Kiểm tra các trường Envelope bắt buộc
    required_envelope = [
        "schema_version", "run_id", "module", "ticker", 
        "as_of_date", "generated_at", "status", "data", 
        "sources", "warnings", "errors"
    ]
    for key in required_envelope:
        if key not in doc:
            errors.append(f"Thiếu trường bắt buộc trong Envelope: '{key}'")

    if doc.get("schema_version") != "1.0":
        errors.append(f"schema_version phải là '1.0', nhận: {doc.get('schema_version')!r}")

    if doc.get("module") != "industry":
        errors.append(f"module phải là 'industry', nhận: {doc.get('module')!r}")

    status = doc.get("status")
    if status not in ["ok", "pending", "partial", "error"]:
        errors.append(f"status phải thuộc ['ok', 'pending', 'partial', 'error'], nhận: {status!r}")

    as_of_date = doc.get("as_of_date")
    if as_of_date is not None:
        try:
            validate_date(as_of_date, "as_of_date")
        except ContractValidationError as e:
            errors.append(str(e))

    # Nếu là status == 'pending' (bản dựng khung rỗng để làm song song)
    if status == "pending":
        return len(errors) == 0, errors

    # 2. Kiểm tra data
    data = doc.get("data")
    if not isinstance(data, dict):
        errors.append("Trường 'data' phải là một dictionary/object JSON.")
        return False, errors

    for req_data_key in ["industry_code", "industry_name", "peers", "metrics", "findings", "risks"]:
        if req_data_key not in data:
            errors.append(f"Thiếu trường bắt buộc trong data: '{req_data_key}'")

    # Thu thập tất cả ID hợp lệ để kiểm tra truy vết bằng chứng (evidence cross-reference)
    valid_source_ids = set()
    valid_metric_ids = set()

    # 3. Kiểm tra sources
    sources = doc.get("sources", [])
    if not isinstance(sources, list):
        errors.append("Trường 'sources' phải là một mảng/list.")
    else:
        for idx, src in enumerate(sources):
            if not isinstance(src, dict):
                errors.append(f"Source tại vị trí {idx} không phải là object.")
                continue
            src_id = src.get("source_id")
            if not src_id or not isinstance(src_id, str):
                errors.append(f"Source tại vị trí {idx} thiếu 'source_id' hợp lệ.")
            else:
                if not src_id.startswith("ind_src_"):
                    errors.append(f"source_id '{src_id}' phải có tiền tố 'ind_src_' theo quy ước Người 2.")
                valid_source_ids.add(src_id)

            if not src.get("url"):
                errors.append(f"Source '{src_id}' thiếu 'url' kiểm chứng.")

            pub_at = src.get("published_at")
            if pub_at is not None:
                try:
                    validate_date(pub_at, f"sources[{idx}].published_at")
                    if as_of_date and pub_at > as_of_date:
                        errors.append(f"Source '{src_id}' có published_at ({pub_at}) > as_of_date ({as_of_date}) vi phạm điều kiện chốt dữ liệu.")
                except ContractValidationError as e:
                    errors.append(str(e))

    # 4. Kiểm tra metrics
    metrics = data.get("metrics", [])
    if isinstance(metrics, list):
        for idx, m in enumerate(metrics):
            if not isinstance(m, dict):
                continue
            m_id = m.get("metric_id")
            if m_id:
                valid_metric_ids.add(m_id)
            val = m.get("value")
            try:
                validate_number_not_percent(val, f"metrics[{idx}].value")
            except ContractValidationError as e:
                errors.append(str(e))

            for sref in m.get("source_refs", []):
                if sref not in valid_source_ids:
                    errors.append(f"Metric '{m_id}' trỏ tới source_ref '{sref}' không tồn tại trong sources.")

    # 5. Kiểm tra peers
    peers = data.get("peers", [])
    if isinstance(peers, list):
        for idx, peer in enumerate(peers):
            if not isinstance(peer, dict):
                continue
            ticker = peer.get("ticker")
            if not ticker or not isinstance(ticker, str):
                errors.append(f"Peer tại vị trí {idx} thiếu 'ticker'.")
            if not peer.get("comparison_basis"):
                errors.append(f"Peer '{ticker}' thiếu 'comparison_basis' (cơ sở so sánh).")
            # Validate metrics inside peer
            p_metrics = peer.get("metrics", {})
            if isinstance(p_metrics, dict):
                for k, v in p_metrics.items():
                    try:
                        validate_number_not_percent(v, f"peer[{ticker}].metrics.{k}")
                    except ContractValidationError as e:
                        errors.append(str(e))

    # 6. Kiểm tra findings & evidence_refs
    findings = data.get("findings", [])
    if isinstance(findings, list):
        for idx, f in enumerate(findings):
            if not isinstance(f, dict):
                continue
            f_id = f.get("finding_id")
            evidence = f.get("evidence_refs", [])
            for ref in evidence:
                if ref not in valid_source_ids and ref not in valid_metric_ids:
                    errors.append(f"Finding '{f_id}' có evidence_ref '{ref}' không tồn tại trong sources hoặc metrics.")

    # 7. Kiểm tra risks & evidence_refs
    risks = data.get("risks", [])
    if isinstance(risks, list):
        for idx, r in enumerate(risks):
            if not isinstance(r, dict):
                continue
            r_id = r.get("risk_id")
            evidence = r.get("evidence_refs", [])
            for ref in evidence:
                if ref not in valid_source_ids and ref not in valid_metric_ids:
                    errors.append(f"Risk '{r_id}' có evidence_ref '{ref}' không tồn tại trong sources hoặc metrics.")

    return len(errors) == 0, errors
