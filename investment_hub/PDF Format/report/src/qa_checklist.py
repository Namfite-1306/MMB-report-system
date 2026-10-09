"""Structural QA for a specific analysis/PDF pair. Research accuracy and layout need review."""
import argparse
import json
import sys
from pathlib import Path
from pdf_generator import validate_analysis, safe_conclusion, SECTIONS


def run_checklist(input_json, output_dir):
    data = json.loads(Path(input_json).read_text(encoding="utf-8-sig"))
    checks = []
    def add(code, status, detail):
        checks.append({"code": code, "status": status, "detail": detail})
    try:
        validate_analysis(data)
        add("AC01", "PASS", "Đủ cấu trúc và định danh snapshot. Luồng chạy web được kiểm tra bằng integration test.")
    except ValueError as exc:
        add("AC01", "FAIL", str(exc))
        return {"checks": checks, "passed": False}
    missing = [k for k, m in data["modules"].items()
               if k != "strategy" and (m["status"] != "ok" or not m["sources"])]
    add("AC02", "WARN" if missing else "MANUAL",
        "Chưa đủ dữ liệu: " + ", ".join(missing) if missing
        else "Cần đối chiếu số và nội dung nguồn gốc; sự tồn tại của nguồn không chứng nhận độ chính xác.")
    display = data.get("display_conclusion")
    safe = safe_conclusion(data)
    if not isinstance(display, dict) or display.get("label") != safe["label"]:
        add("AC03", "FAIL", "Thiếu display_conclusion an toàn hoặc kết luận không khớp điều kiện sử dụng.")
    elif safe["label"] == "insufficient_data":
        add("AC03", "WARN", "Đúng cơ chế chặn kết luận; chưa đủ dữ liệu để nghiệm thu chiến lược.")
    else:
        strategy = data["modules"]["strategy"]["data"]
        traced = strategy.get("theory_sources") and strategy.get("rules") and safe.get("evidence_refs")
        add("AC03", "PASS" if traced else "FAIL", "Kiểm tra tồn tại lý thuyết, quy tắc và bằng chứng; chất lượng cần review.")
    try:
        from pypdf import PdfReader
        directory = Path(output_dir)
        manifest = json.loads((directory / "report_manifest.json").read_text(encoding="utf-8"))
        for field, expected in {"run_id": data.get("run_id"), "ticker": data["request"].get("ticker"),
                                "as_of_date": data["request"].get("as_of_date"),
                                "overall_status": data["overall_status"], "schema_version": "1.0",
                                "pdf_filename": "report.pdf"}.items():
            if manifest.get(field) != expected:
                raise ValueError("Manifest không khớp " + field)
        if not set(SECTIONS).issubset(manifest.get("sections_present", [])):
            raise ValueError("Manifest thiếu phần bắt buộc.")
        reader = PdfReader(directory / "report.pdf")
        if not reader.pages or not any("PHÂN TÍCH" in (page.extract_text() or "") for page in reader.pages):
            raise ValueError("PDF rỗng hoặc không trích được chữ tiếng Việt.")
        for page in reader.pages:
            for font_ref in page["/Resources"].get("/Font", {}).values():
                font = font_ref.get_object()
                if font.get("/BaseFont") == "/Helvetica":
                    # ReportLab emits an unused default font; visible text uses embedded Hub fonts.
                    continue
                descendants = font.get("/DescendantFonts")
                if descendants:
                    font = descendants[0].get_object()
                descriptor = font.get("/FontDescriptor")
                if not descriptor or not any(k in descriptor.get_object() for k in ("/FontFile", "/FontFile2", "/FontFile3")):
                    raise ValueError("Font sử dụng chưa được nhúng.")
        add("AC04", "PASS", f"Đọc được {len(reader.pages)} trang, chữ Việt và font nhúng; cần render để kiểm bảng/tràn.")
    except Exception as exc:
        add("AC04", "FAIL", str(exc))
    inconsistent = (data["overall_status"] == "ok" and any(m["status"] != "ok" or m["errors"]
                                                        for m in data["modules"].values()))
    add("AC06", "FAIL" if inconsistent else "PASS", "Kiểm tra trạng thái snapshot; các ca sai mã/chia 0 cần test nghiệp vụ.")
    for code, detail in [
        ("AC05", "Kiểm tra sáng tạo bằng demo."),
        ("AC07", "Kiểm tra tái lập với snapshot và môi trường đã ghi nhận."),
        ("AC08", "Kiểm tra gói nộp và quyền truy cập."),
    ]:
        add(code, "MANUAL", detail)
    return {"checks": checks, "passed": not any(c["status"] == "FAIL" for c in checks)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = run_checklist(args.input, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except Exception as exc:
        print("QA: " + str(exc), file=sys.stderr)
        sys.exit(1)
