"""Vector dashboards from the report snapshot; no external data fetch."""
import math
from datetime import date
from reportlab.graphics.shapes import Drawing, Line, PolyLine, String, Rect
from reportlab.lib import colors

GREEN = colors.HexColor("#3d6e1a")
CYAN = colors.HexColor("#126d65")
PURPLE = colors.HexColor("#7151ad")
MUTED = colors.HexColor("#627084")
GRID = colors.HexColor("#d5dde3")


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value)


def dashboard_data(analysis):
    request = analysis["request"]
    company = analysis["modules"]["company"]
    prices = sorted([dict(p) for p in company["data"].get("price_series", [])
                     if request["period_start"] <= p["date"] <= request["period_end"]
                     and p["date"] <= request["as_of_date"]], key=lambda p: p["date"])
    for i, p in enumerate(prices):
        p["close"] = p["close"] if numeric(p.get("close")) else None
        p["volume"] = p["volume"] if numeric(p.get("volume")) and p["volume"] >= 0 else None
        window = prices[max(0, i - 19):i + 1]
        p["ma20"] = sum(r["close"] for r in window) / 20 if len(window) == 20 and all(numeric(r.get("close")) for r in window) else None
    sources = {s["source_id"]: s for s in company["sources"]}
    groups = {}
    for r in company["data"].get("financials", []):
        if (r.get("verified") is not True or r.get("frequency") != request.get("financial_basis", "annual")
                or r.get("statement_scope") != request.get("statement_scope", "consolidated")
                or r.get("unit") != "VND" or r["period_end"] > request["as_of_date"]
                or r["item_id"] not in ("revenue", "net_profit", "cfo")):
            continue
        refs = [sources.get(ref) for ref in r.get("source_refs", [])]
        if not refs or any(not s or not s["publication_date_verified"] or not s["published_at"]
                           or s["published_at"][:10] > request["as_of_date"] for s in refs):
            continue
        key = (r["period_start"], r["period_end"])
        groups.setdefault(key, {})[r["item_id"]] = r["value"] if numeric(r["value"]) else None
    periods = [(key, groups[key]) for key in sorted(groups, key=lambda key: key[1])[-3:]]
    return prices, periods


def frame(width, minimum, maximum, first="", last="", unit=""):
    drawing = Drawing(width, 180)
    left, right, bottom, top = 55, width - 12, 28, 155
    for i in range(5):
        y = bottom + (top - bottom) * i / 4
        value = minimum + (maximum - minimum) * i / 4
        drawing.add(Line(left, y, right, y, strokeColor=GRID, strokeWidth=.4))
        label = f"{value:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".")
        drawing.add(String(left - 7, y - 3, label, fontName="HubRegular", fontSize=7, fillColor=MUTED, textAnchor="end"))
    drawing.add(String(left, 8, first, fontName="HubRegular", fontSize=7, fillColor=MUTED))
    drawing.add(String(right, 8, last, fontName="HubRegular", fontSize=7, fillColor=MUTED, textAnchor="end"))
    drawing.add(String(left, 168, unit, fontName="HubRegular", fontSize=8, fillColor=MUTED))
    def y(value):
        return bottom + (value - minimum) / (maximum - minimum) * (top - bottom)
    return drawing, left, right, bottom, y


def domain(values, zero=False):
    minimum, maximum = min(values), max(values)
    if zero:
        minimum, maximum = min(0, minimum), max(0, maximum)
    padding = (maximum - minimum or abs(maximum) * .05 or 1) * .08
    return (0 if zero and minimum == 0 else minimum - padding), maximum + padding


def market_charts(prices, width):
    if not prices or not any(numeric(p["close"]) for p in prices):
        return []
    values = [p[key] for p in prices for key in ("close", "ma20") if numeric(p[key])]
    low, high = domain(values)
    drawing, left, right, bottom, y = frame(width, low, high, prices[0]["date"], prices[-1]["date"], "VND / cổ phiếu | Đóng cửa: xanh lá; MA20: tím")
    start = date.fromisoformat(prices[0]["date"]).toordinal()
    span = date.fromisoformat(prices[-1]["date"]).toordinal() - start
    def x(p):
        return left + (date.fromisoformat(p["date"]).toordinal() - start) / span * (right - left) if span else (left + right) / 2
    for key, color in (("close", GREEN), ("ma20", PURPLE)):
        points = []
        def flush():
            if len(points) >= 4:
                drawing.add(PolyLine(points[:], strokeColor=color, strokeWidth=1.1))
            elif len(points) == 2:
                drawing.add(Rect(points[0]-1,points[1]-1,2,2,fillColor=color,strokeColor=color))
        for p in prices:
            if numeric(p[key]):
                points.extend((x(p), y(p[key])))
            else:
                flush()
                points = []
        flush()
    charts = [("Lịch sử giá và MA20", drawing)]
    if any(numeric(p["volume"]) for p in prices):
        maximum = max(p["volume"] for p in prices if numeric(p["volume"])) or 1
        volume, left, right, bottom, y = frame(width, 0, maximum/1e6, prices[0]["date"], prices[-1]["date"], "Triệu cổ phiếu")
        bar_width = max(.35, min(10, (right-left)/len(prices)*.7))
        for p in prices:
            if numeric(p["volume"]):
                volume.add(Rect(x(p)-bar_width/2,bottom,bar_width,y(p["volume"]/1e6)-bottom,fillColor=CYAN,strokeColor=None))
        charts.append(("Khối lượng giao dịch", volume))
    return charts


def financial_chart(periods, width):
    keys = ("revenue", "net_profit", "cfo")
    values = [r[k]/1e9 for key, r in periods for k in keys if numeric(r.get(k))]
    if not values:
        return None
    minimum, maximum = domain(values, True)
    drawing, left, right, bottom, y = frame(width, minimum, maximum, unit="Tỷ VND | Doanh thu: xanh lá; LNST: xanh ngọc; CFO: tím")
    zero = y(0)
    drawing.add(Line(left,zero,right,zero,strokeColor=MUTED,strokeWidth=.6))
    group_width = (right-left)/len(periods)
    bar_width = min(30,group_width/5)
    for i,(key,r) in enumerate(periods):
        center = left+group_width*(i+.5)
        for j,(item,color) in enumerate(zip(keys,(GREEN,CYAN,PURPLE))):
            if numeric(r.get(item)):
                top = y(r[item]/1e9)
                drawing.add(Rect(center+(j-1)*bar_width*1.25-bar_width/2,min(top,zero),bar_width,abs(top-zero),fillColor=color,strokeColor=None))
        drawing.add(String(center,8,key[1],fontName="HubRegular",fontSize=8,fillColor=MUTED,textAnchor="middle"))
    return drawing
