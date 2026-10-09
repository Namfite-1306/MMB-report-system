"""PDF renderer adapted from member 6 for MMB Analysis schema v1.0.

No data collection or financial calculations: renders the assembled snapshot.
Uses ReportLab and embedded local TrueType fonts for Vietnamese on Windows.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle
if __package__:
    from .dashboard import dashboard_data, market_charts, financial_chart
else:
    from dashboard import dashboard_data, market_charts, financial_chart

BASE_DIR = Path(__file__).resolve().parent.parent
MODULES = ("macro", "industry", "company", "strategy")
SECTIONS = [*MODULES, "risks", "sources"]
NAMES = {"macro": "Tổng quan Vĩ mô", "industry": "Phân tích Ngành",
         "company": "Phân tích Doanh nghiệp", "strategy": "Chiến lược Đầu tư"}
STATUS = {"pending": "Đang chờ", "partial": "Chưa hoàn chỉnh",
          "error": "Có lỗi", "ok": "Hoàn chỉnh"}
LABELS = {"attractive": "Có cơ hội", "watchlist": "Theo dõi",
          "unattractive": "Chưa hấp dẫn", "insufficient_data": "Chưa đủ dữ liệu"}
VN_TZ = timezone(timedelta(hours=7))


def validate_analysis(data):
    if not isinstance(data, dict) or data.get("schema_version") != "1.0":
        raise ValueError("analysis cần schema_version=1.0.")
    if not isinstance(data.get("request"), dict):
        raise ValueError("analysis thiếu request.")
    modules = data.get("modules")
    if not isinstance(modules, dict) or any(k not in modules for k in MODULES):
        raise ValueError("analysis cần đủ macro, industry, company, strategy.")
    if data.get("overall_status") not in STATUS:
        raise ValueError("overall_status không hợp lệ.")
    for key in MODULES:
        m = modules[key]
        if not isinstance(m, dict) or not isinstance(m.get("data"), dict):
            raise ValueError(f"{key} thiếu data.")
        if m.get("status") not in STATUS:
            raise ValueError(f"{key}.status không hợp lệ.")
        for field in ("sources", "warnings", "errors"):
            if not isinstance(m.get(field), list):
                raise ValueError(f"{key}.{field} cần mảng.")
        # Reject another run's snapshot rather than silently patching identities.
        for field, expected in (("run_id", data.get("run_id")),
                                ("ticker", data["request"].get("ticker")),
                                ("as_of_date", data["request"].get("as_of_date"))):
            if m.get(field) != expected:
                raise ValueError(f"{key}.{field} không khớp analysis.")
    for field in ("warnings", "errors"):
        if not isinstance(data.get(field), list) or not all(isinstance(x, str) for x in data[field]):
            raise ValueError(f"analysis.{field} cần mảng chuỗi.")
    return data


def safe_conclusion(data):
    """Never promote the raw strategy recommendation to the report."""
    display = data.get("display_conclusion")
    usable = (data.get("conclusion_usable") is True and data["overall_status"] == "ok"
              and all(data["modules"][k]["status"] == "ok" for k in MODULES)
              and not data["warnings"] and not data["errors"])
    if (usable and isinstance(display, dict) and display.get("label") in LABELS
            and isinstance(display.get("rationale"), str) and display["rationale"].strip()):
        return display
    # Preserve the assembled explanation for a blocked recommendation.
    if isinstance(display, dict) and display.get("label") == "insufficient_data":
        return display
    return {"label": "insufficient_data",
            "rationale": "Chưa đủ dữ liệu/bằng chứng được kiểm chứng để sử dụng kết luận.",
            "horizon": data["request"].get("investment_horizon"), "evidence_refs": []}


def register_fonts():
    custom = os.environ.get("PDF_FONT_DIR")
    candidates = []
    if custom:
        candidates.extend([(Path(custom) / "arial.ttf", Path(custom) / "arialbd.ttf"),
                           (Path(custom) / "DejaVuSans.ttf", Path(custom) / "DejaVuSans-Bold.ttf")])
    candidates.extend([
        (Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/arial.ttf",
         Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/arialbd.ttf"),
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
         Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
        (Path("/Library/Fonts/Arial.ttf"), Path("/Library/Fonts/Arial Bold.ttf")),
    ])
    for regular, bold in candidates:
        if regular.is_file() and bold.is_file():
            pdfmetrics.registerFont(TTFont("HubRegular", str(regular)))
            pdfmetrics.registerFont(TTFont("HubBold", str(bold)))
            pdfmetrics.registerFontFamily("HubRegular", normal="HubRegular", bold="HubBold",
                                         italic="HubRegular", boldItalic="HubBold")
            return
    raise RuntimeError("Không tìm thấy font tiếng Việt. Đặt PDF_FONT_DIR tới Arial hoặc DejaVu Sans.")


def text(value):
    if value is None:
        return "Chưa có"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    return str(value)


def refs(value):
    return ", ".join(map(str, value or [])) or "Chưa có"


def period(row):
    return f'{row.get("period_start") or "?"} - {row.get("period_end") or "?"}'


def generate_manifest(data, pdf_path):
    return {
        "schema_version": "1.0", "run_id": data.get("run_id"),
        "ticker": data["request"].get("ticker"), "as_of_date": data["request"].get("as_of_date"),
        "overall_status": data["overall_status"], "generated_at": datetime.now(VN_TZ).isoformat(),
        # A pending/error section is still present in the PDF and must be listed.
        "sections_present": SECTIONS.copy(), "warnings": data["warnings"].copy(),
        "pdf_filename": Path(pdf_path).name,
        "renderer": "reportlab", "conclusion_label": safe_conclusion(data)["label"]
    }


def generate_pdf(data, output_pdf, output_manifest=None):
    validate_analysis(data)
    register_fonts()
    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    body = ParagraphStyle("Body", fontName="HubRegular", fontSize=9.5, leading=14.5,
                          textColor=colors.HexColor("#263345"), spaceAfter=7,
                          splitLongWords=True)
    cell = ParagraphStyle("Cell", parent=body, fontSize=7.5, leading=10.5,
                          spaceAfter=0, wordWrap="CJK")
    headcell = ParagraphStyle("HeadCell", parent=cell, fontName="HubBold",
                              textColor=colors.white)
    title = ParagraphStyle("Title", parent=body, fontName="HubBold", fontSize=20,
                           leading=25, spaceAfter=15, textColor=colors.HexColor("#183c64"))
    heading = ParagraphStyle("Heading", parent=body, fontName="HubBold", fontSize=14,
                             leading=19, spaceBefore=18, spaceAfter=9, keepWithNext=True,
                             textColor=colors.HexColor("#24537c"))
    subheading = ParagraphStyle("Subheading", parent=heading, fontSize=11, leading=15,
                                spaceBefore=10, spaceAfter=7)
    table_note = ParagraphStyle("TableNote", parent=body, keepWithNext=True)
    story = []
    width = A4[0] - 36 * mm

    def p(value, style=body):
        # Everything from uploaded JSON is literal text, never ReportLab markup.
        return Paragraph(escape(text(value)).replace("\n", "<br/>"), style)

    def add(value, style=body):
        story.append(p(value, style))

    def table(headers, rows, weights):
        if not rows:
            add("Chưa có dữ liệu được ghi nhận.")
            return
        total = sum(weights)
        items = [[p(h, headcell) for h in headers]]
        items.extend([[p(v, cell) for v in row] for row in rows])
        grid = LongTable(items, colWidths=[width * w / total for w in weights],
                         repeatRows=1, hAlign="LEFT", splitInRow=1)
        grid.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24537c")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5f8")]),
            ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#d4dde6")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
        ]))
        story.extend([grid, Spacer(1, 4 * mm)])

    request = data["request"]
    add("MMB ANALYSIS", title)
    add("BÁO CÁO PHÂN TÍCH CƠ HỘI ĐẦU TƯ", subheading)
    add(request.get("ticker") or "CHƯA CHỐT MÃ", heading)
    table(["Thông tin", "Input chung"], [
        ["Sàn / Ngành", f'{request.get("exchange") or "Chưa chốt"} / {request.get("industry_name") or "Chưa chốt"}'],
        ["Ngày chốt / Kỳ", f'{request.get("as_of_date") or "Chưa chốt"} / {period(request)}'],
        ["Thời hạn / Tiền tệ", f'{request.get("investment_horizon") or "Chưa chốt"} / {request.get("currency") or "VND"}'],
        ["Trạng thái / Run", f'{STATUS[data["overall_status"]]} / {data.get("run_id") or "Bản xem trước chưa có run"}'],
        ["Schema", data["schema_version"]]
    ], [1, 3])
    conclusion = safe_conclusion(data)
    add("Kết luận đã kiểm tra: " + LABELS[conclusion["label"]], subheading)
    add(conclusion.get("rationale"))
    add("Thời hạn: " + text(conclusion.get("horizon")))
    if conclusion.get("evidence_refs"):
        add("Bằng chứng: " + refs(conclusion["evidence_refs"]))

    add("Dashboard phân tích", heading)
    prices, financial_periods = dashboard_data(data)
    charts = market_charts(prices, width)
    if not charts:
        add("Chưa có dữ liệu giá để vẽ dashboard.")
    for name, drawing in charts:
        add(name, subheading)
        story.append(drawing)
    if charts:
        add(f"Toàn kỳ {request['period_start']} - {request['period_end']}; {len(prices)} phiên. MA20 dùng 20 phiên có trong dữ liệu, chỉ dùng thông tin tới phiên tính; không lấp giá thiếu/ngày nghỉ. Cơ sở điều chỉnh giá: " + ", ".join(sorted({p.get("adjustment_basis", "Chưa xác minh") for p in prices})))
        add("Đồ thị giá mô tả dữ liệu nhà cung cấp; chưa phải lợi suất đầu tư gồm cổ tức và chi phí giao dịch.")
    finance = financial_chart(financial_periods, width)
    add("Doanh thu, lợi nhuận sau thuế và dòng tiền kinh doanh", subheading)
    if finance:
        story.append(finance)
    else:
        add("Chưa có BCTC đúng kỳ/phạm vi và nguồn đủ điều kiện để vẽ biểu đồ.")
    add(f"BCTC: {request.get('financial_basis', 'annual')} / {request.get('statement_scope', 'consolidated')}. Chỉ dùng số đã đối chiếu và công bố trước ngày chốt; không trộn YTD/quý với năm, không quy đổi YTD thành năm.")
    for index, key in enumerate(MODULES, 1):
        m = data["modules"][key]
        d = m["data"]
        add(f"{index}. {NAMES[key]} - {STATUS[m['status']]}", heading)
        for warning in m["warnings"]:
            add("Cảnh báo: " + warning)
        for error in m["errors"]:
            add("Lỗi: " + error)
        if key != "strategy":
            add("Bảng chỉ số", subheading)
            table(["Chỉ số", "Giá trị", "Đơn vị / Tần suất", "Kỳ", "Công thức / Nguồn"], [
                [v.get("metric_id"), v.get("value"),
                 f'{v.get("unit") or "?"} / {v.get("frequency") or "?"}', period(v),
                 f'{v.get("formula_id") or "Quan sát"} / {refs(v.get("source_refs"))}']
                for v in d.get("metrics", [])
            ], [1.25, .7, 1, 1.15, 1.6])
            add("Giá trị giữ nguyên đơn vị input; tỷ lệ thập phân 0.12 tương ứng 12%. Giá trị thiếu là Chưa có, không thay bằng 0.")
        if key == "industry" and d.get("peers"):
            add("Doanh nghiệp so sánh", subheading)
            table(["Doanh nghiệp", "Thông tin bàn giao"], [
                [peer.get("ticker", "Chưa có") if isinstance(peer, dict) else peer, peer]
                for peer in d["peers"]], [1, 4])
        if key == "company":
            prices = d.get("price_series", [])
            add("Lịch sử giá", subheading)
            shown = sorted(prices, key=lambda row: row.get("date", ""))[-10:]
            add(f"Hiển thị {len(shown)} phiên có ngày gần nhất trong tổng {len(prices)} phiên bàn giao; không nội suy.", table_note)
            table(["Ngày", "Đóng cửa", "Khối lượng", "Cơ sở điều chỉnh", "Nguồn"], [
                [r.get("date"), r.get("close"), r.get("volume"),
                 r.get("adjustment_basis"), refs(r.get("source_refs"))] for r in shown
            ], [1, 1, 1, 1.5, 1.5])
            add("Báo cáo tài chính", subheading)
            table(["Khoản mục", "Giá trị / Đơn vị", "Kỳ", "Phạm vi", "Nguồn"], [
                [r.get("item_id"), f'{text(r.get("value"))} / {r.get("unit") or "?"}',
                 period(r), r.get("statement_scope"), refs(r.get("source_refs"))]
                for r in d.get("financials", [])
            ], [1.2, 1, 1.2, 1, 1.6])
        if key == "strategy":
            add("Cơ sở lý thuyết đầu tư", subheading)
            for item in d.get("theory_sources", []):
                add(item)
            if not d.get("theory_sources"):
                add("Chưa có lý thuyết được bàn giao.")
            add("Quy tắc đánh giá", subheading)
            table(["Rule ID", "Lý thuyết", "Đầu vào", "Công thức", "Ngưỡng"], [
                [r.get("rule_id"), refs(r.get("theory_refs")), refs(r.get("input_metric_ids")),
                 r.get("formula"), r.get("thresholds")]
                if isinstance(r, dict) else ["Chưa có ID", "", "", r, ""]
                for r in d.get("rules", [])
            ], [1, 1, 1.2, 1.6, 1.2])
            for rule in d.get("rules", []):
                if isinstance(rule, dict) and rule.get("status"):
                    add(f'{rule.get("rule_id")}: {rule["status"]}', subheading)
                    add(rule.get("explanation"))
                    if rule.get("values") is not None:
                        table(["Kết quả tính", "Giá trị"], [
                            [name, value] for name, value in rule["values"].items()
                        ], [2, 3])
                    if rule.get("evidence_refs"):
                        add("Nguồn đầu vào: " + refs(rule["evidence_refs"]))
            add("Bằng chứng chiến lược: " + refs(d.get("evidence_refs")))
            add("Kết luận sử dụng trong báo cáo: " + LABELS[conclusion["label"]], subheading)
            add(conclusion.get("rationale"))
            if not data.get("conclusion_usable"):
                add("Kết luận thô của module chưa đủ điều kiện sử dụng; báo cáo không trình bày nó như khuyến nghị.")
        if d.get("findings"):
            add("Nhận định", subheading)
            for item in d["findings"]:
                add(item.get("text") if isinstance(item, dict) else item)
                if isinstance(item, dict) and item.get("evidence_refs"):
                    add("Bằng chứng: " + refs(item["evidence_refs"]))

    add("5. Rủi ro, cảnh báo và giới hạn", heading)
    risk_count = 0
    for key in MODULES:
        for item in data["modules"][key]["data"].get("risks", []):
            risk_count += 1
            add(NAMES[key] + ": " + text(item.get("text") if isinstance(item, dict) else item))
            if isinstance(item, dict) and item.get("evidence_refs"):
                add("Bằng chứng: " + refs(item["evidence_refs"]))
    if not risk_count:
        add("Chưa có rủi ro được bàn giao; không đồng nghĩa với không có rủi ro.")
    for value in data["warnings"]:
        add("Cảnh báo tổng hợp: " + value)
    for value in data["errors"]:
        add("Lỗi tổng hợp: " + value)
    add("Báo cáo trình bày snapshot đầu vào, không tự kiểm chứng nội dung website nguồn hoặc đánh giá hiệu quả mô hình đầu tư.")

    add("6. Danh mục nguồn tham khảo", heading)
    referenced = set()
    def gather_refs(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ("source_refs", "evidence_refs") and isinstance(item, list):
                    referenced.update(item)
                elif key not in ("financial_candidates", "price_series", "news"):
                    gather_refs(item)
        elif isinstance(value, list):
            for item in value:
                gather_refs(item)
    for key in MODULES:
        gather_refs(data["modules"][key]["data"])
    for row in sorted(data["modules"]["company"]["data"].get("price_series", []), key=lambda r: r.get("date", ""))[-10:]:
        referenced.update(row.get("source_refs", []))
    all_sources = [(key, source) for key in MODULES for source in data["modules"][key]["sources"]]
    sources = [(key, source) for key, source in all_sources if source["source_id"] in referenced or key == "strategy"]
    add(f"Hiển thị {len(sources)} nguồn được dẫn trong bảng/nhận định của PDF trên tổng {len(all_sources)} nguồn bàn giao. Danh mục đầy đủ, các phiên giá còn lại và candidate BCTC nằm trong analysis.json tải cùng báo cáo.", table_note)
    table(["ID / Module", "Nguồn / Vị trí", "Công bố / Truy cập", "Xác minh ngày"], [
        [f'{source.get("source_id")} / {key}',
         f'{source.get("title")}\n{source.get("url")}\n{source.get("locator") or ""}',
         f'{text(source.get("published_at"))}\n{source.get("retrieved_at")}',
         "Đã xác minh" if source.get("publication_date_verified") else "Chưa xác minh"]
        for key, source in sources
    ], [1.2, 2.6, 1.5, 1])
    add("Nhãn đánh giá là quy ước của nhóm, không phải cam kết lợi nhuận.")

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("HubRegular", 8)
        canvas.setFillColor(colors.HexColor("#627084"))
        canvas.drawString(18 * mm, 12 * mm, "MMB Analysis | Schema 1.0")
        canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, f"Trang {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(str(output_pdf), pagesize=A4, rightMargin=18 * mm,
                            leftMargin=18 * mm, topMargin=17 * mm, bottomMargin=20 * mm,
                            title="Phân tích " + (request.get("ticker") or "chưa chốt mã"),
                            author="MMB Analysis", allowSplitting=True)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    manifest = generate_manifest(data, output_pdf)
    if output_manifest:
        Path(output_manifest).parent.mkdir(parents=True, exist_ok=True)
        Path(output_manifest).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Tạo PDF từ analysis.json của MMB Analysis.")
    parser.add_argument("input", nargs="?", default=str(BASE_DIR / "inputs/pending_analysis.json"))
    parser.add_argument("--output-dir", default=str(BASE_DIR / "outputs"))
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    directory = Path(args.output_dir)
    manifest = generate_pdf(data, directory / "report.pdf", directory / "report_manifest.json")
    print(json.dumps({"pdf_filename": "report.pdf", "manifest": manifest}, ensure_ascii=False))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        main()
    except Exception as exc:
        print("PDF: " + str(exc), file=sys.stderr)
        sys.exit(1)
