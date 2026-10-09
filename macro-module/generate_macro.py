#!/usr/bin/env python
"""CLI tạo macro.json và tùy chọn macro_data.xlsx từ cùng một kết quả phân tích."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from macro_module import build_macro_result, load_json, write_json

ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tạo output vĩ mô cho một mã cổ phiếu Việt Nam")
    parser.add_argument("--input", default=str(ROOT / "examples" / "input.sample.json"))
    parser.add_argument("--data-file", default=str(ROOT / "data" / "verified_macro_data.json"))
    parser.add_argument("--industry-map", default=str(ROOT / "config" / "industry_mapping.json"))
    parser.add_argument("--output", default=str(ROOT / "macro.json"), help="Đường dẫn JSON đầu ra")
    parser.add_argument("--excel-output", help="Nếu truyền, xuất thêm workbook từ cùng kết quả dùng cho JSON")
    parser.add_argument("--node-command", default=os.environ.get("MACRO_NODE_COMMAND", "node"))
    parser.add_argument("--excel-builder", default=str(ROOT / "tools" / "build_macro_excel.mjs"))
    parser.add_argument("--excel-preview-dir", help="Thư mục PNG kiểm tra trực quan; chỉ dùng khi QA")
    parser.add_argument("--force", action="store_true", help="Cho phép cập nhật các output đã tồn tại")
    return parser.parse_args()


def _ensure_outputs_available(paths: list[Path], force: bool) -> None:
    existing = [str(path) for path in paths if path.exists()]
    if existing and not force:
        raise FileExistsError("Output đã tồn tại; dùng --force để cập nhật có chủ đích: " + ", ".join(existing))


def _resolve_command(command: str) -> str:
    direct = Path(command)
    if direct.exists():
        return str(direct.resolve())
    resolved = shutil.which(command)
    if resolved:
        return resolved
    raise FileNotFoundError(f"Không tìm thấy Node.js: {command}")


def _export_excel(result: dict, args: argparse.Namespace) -> None:
    node = _resolve_command(args.node_command)
    builder = Path(args.excel_builder).resolve()
    if not builder.exists():
        raise FileNotFoundError(f"Không tìm thấy Excel builder: {builder}")

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".macro-result.json",
            prefix="macro-",
            dir=ROOT,
            delete=False,
        ) as handle:
            json.dump(result, handle, ensure_ascii=False, allow_nan=False)
            temporary_path = Path(handle.name)

        command = [
            node,
            str(builder),
            "--result",
            str(temporary_path),
            "--output",
            str(Path(args.excel_output).resolve()),
        ]
        if args.force:
            command.append("--force")
        if args.excel_preview_dir:
            command.extend(["--preview-dir", str(Path(args.excel_preview_dir).resolve())])
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if completed.stdout.strip():
            print(completed.stdout.strip())
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def main() -> int:
    # Bảo đảm thông báo tiếng Việt hiển thị đúng trên Windows.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    json_output = Path(args.output).resolve()
    excel_output = Path(args.excel_output).resolve() if args.excel_output else None

    try:
        _ensure_outputs_available(
            [path for path in (json_output, excel_output) if path is not None],
            args.force,
        )
        payload = load_json(args.input)
        dataset = load_json(args.data_file)
        industry_mapping = load_json(args.industry_map)
        result = build_macro_result(payload, dataset, industry_mapping)
        if excel_output:
            _export_excel(result, args)
        write_json(result, json_output, force=args.force)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        print(f"Lỗi xuất Excel: {detail}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 2

    print(f"Đã ghi JSON: {json_output} (status={result['status']})")
    if excel_output:
        print(f"Đã ghi Excel: {excel_output}")
    dataset_meta = result.get("data", {}).get("metadata", {}).get("dataset", {})
    print(
        "Chế độ dữ liệu: tái tạo output từ snapshot cục bộ "
        f"(verified_through={dataset_meta.get('verified_through')}); không tải dữ liệu mới."
    )
    return 0 if result["status"] != "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
