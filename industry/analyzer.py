"""Analyzer engine for Người 2 (Module Ngành - Industry Module).
Thực thi phân tích ngành, so sánh doanh nghiệp cùng ngành (peers),
tính toán chỉ số định giá và rủi ro ngành, tuân thủ 100% hợp đồng dữ liệu V1.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
from typing import Any, Dict, Optional

from industry.data_loader import resolve_sector_for_ticker
from industry.schema import validate_industry_output, validate_date


def get_current_timestamp_vn() -> str:
    """Trả về thời gian hiện tại chuẩn ISO 8601 có múi giờ Việt Nam +07:00."""
    now_vn = dt.datetime.now(dt.timezone(dt.timedelta(hours=7)))
    return now_vn.isoformat()


def build_pending_industry_output(
    run_id: Optional[str] = None,
    ticker: Optional[str] = None,
    as_of_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Tạo output khung rỗng 'pending' theo đúng quy ước dòng 27-28 Sheet 2 để phối hợp song song."""
    return {
        "schema_version": "1.0",
        "run_id": run_id,
        "module": "industry",
        "ticker": ticker,
        "as_of_date": as_of_date,
        "generated_at": get_current_timestamp_vn(),
        "status": "pending",
        "data": {
            "industry_code": None,
            "industry_name": None,
            "peers": [],
            "metrics": [],
            "findings": [],
            "risks": [],
        },
        "sources": [],
        "warnings": [
            "Chưa có dữ liệu thật hoặc đang ở trạng thái pending xây luồng song song"
        ],
        "errors": [],
    }


def analyze_industry(request: Dict[str, Any]) -> Dict[str, Any]:
    """Hàm lõi phân tích ngành nhận request dictionary và trả về envelope industry.json chuẩn V1."""
    schema_version = request.get("schema_version", "1.0")
    run_id = request.get("run_id") or f"run_ind_{int(dt.datetime.now().timestamp())}"
    ticker = request.get("ticker")
    as_of_date = request.get("as_of_date") or dt.date.today().isoformat()
    mode = request.get("mode", "ok")

    # Kiểm tra nếu request yêu cầu pending hoặc thiếu mã cổ phiếu
    if mode == "pending" or not ticker:
        return build_pending_industry_output(run_id=run_id, ticker=ticker, as_of_date=as_of_date)

    ticker = str(ticker).strip().upper()
    try:
        validate_date(as_of_date, "as_of_date")
    except Exception as e:
        return {
            "schema_version": "1.0",
            "run_id": run_id,
            "module": "industry",
            "ticker": ticker,
            "as_of_date": as_of_date,
            "generated_at": get_current_timestamp_vn(),
            "status": "error",
            "data": None,
            "sources": [],
            "warnings": [],
            "errors": [f"Ngày chốt as_of_date không hợp lệ: {e}"],
        }

    # Tải hồ sơ ngành từ data_loader
    profile = resolve_sector_for_ticker(ticker=ticker, as_of_date=as_of_date)

    # Đóng gói theo chuẩn envelope chung
    result: Dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": str(run_id),
        "module": "industry",
        "ticker": ticker,
        "as_of_date": as_of_date,
        "generated_at": get_current_timestamp_vn(),
        "status": "ok",
        "data": {
            "industry_code": profile.industry_code,
            "industry_name": profile.industry_name,
            "sector_cycle_stage": profile.sector_cycle_stage,
            "peers": [p.to_dict() for p in profile.peers],
            "metrics": [m.to_dict() for m in profile.metrics],
            "findings": [f.to_dict() for f in profile.findings],
            "risks": [r.to_dict() for r in profile.risks],
        },
        "sources": [s.to_dict() for s in profile.sources],
        "warnings": [],
        "errors": [],
    }

    # Tự kiểm tra hợp đồng (contract verification)
    is_valid, validation_errors = validate_industry_output(result)
    if not is_valid:
        result["status"] = "partial" if result["data"] else "error"
        result["warnings"].extend(validation_errors)

    return result


def main():
    parser = argparse.ArgumentParser(description="Người 2: Module phân tích ngành và so sánh peers.")
    parser.add_argument("--ticker", default="HPG", help="Mã cổ phiếu cần phân tích (ví dụ HPG, FPT, VCB)")
    parser.add_argument("--as-of-date", default="2026-10-09", help="Ngày chốt dữ liệu (YYYY-MM-DD)")
    parser.add_argument("--run-id", default=None, help="Mã phiên chạy do Người 5 cấp")
    parser.add_argument("--request", type=pathlib.Path, help="Đường dẫn tới file request.json từ Người 5")
    parser.add_argument("--pending", action="store_true", help="Xuất khung rỗng pending để làm song song")
    parser.add_argument("-o", "--output", type=pathlib.Path, default=pathlib.Path("industry.json"), help="File output (mặc định industry.json)")

    args = parser.parse_args()

    if args.request and args.request.exists():
        req_doc = json.loads(args.request.read_text(encoding="utf-8"))
    else:
        req_doc = {
            "schema_version": "1.0",
            "run_id": args.run_id or f"run_cli_{int(dt.datetime.now().timestamp())}",
            "ticker": args.ticker,
            "as_of_date": args.as_of_date,
            "mode": "pending" if args.pending else "ok",
        }

    out = analyze_industry(req_doc)

    # Ghi file JSON UTF-8
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        print(f"[OK] Da xuat module nganh ra: {args.output.resolve()} (status: {out['status']}, ticker: {out['ticker']})")
    except Exception:
        pass


if __name__ == "__main__":
    main()
