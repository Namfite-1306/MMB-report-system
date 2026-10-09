import calendar
import copy
import json
import math
import statistics
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent


class ContractError(ValueError):
    pass


class MissingData(ValueError):
    pass


def check(condition, message):
    if not condition:
        raise ContractError(message)


def day(value):
    check(isinstance(value, str), "Ngày phải là YYYY-MM-DD.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ContractError(f"Ngày không hợp lệ: {value}") from exc
    check(parsed.isoformat() == value, "Ngày phải đúng YYYY-MM-DD.")
    return parsed


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value)


def ratio(numerator, denominator, positive_denominator=True):
    if denominator == 0 or (positive_denominator and denominator < 0):
        raise MissingData("Mẫu số không phù hợp; kết quả để null.")
    return numerator / denominator


def defaults():
    formulas = {
        "macro": "change = current - previous; effect follows sourced mechanism",
        "industry": "industry_growth = revenue_current / revenue_previous - 1",
        "fundamental": "growth, margins, ROE, ROA, leverage, liquidity, CFO",
        "value": "margin_of_safety = 1 - price / intrinsic_value",
        "relative_valuation": "relative_value = EPS or BVPS * peer_median_multiple",
        "momentum": "adjusted_month_end_price / adjusted_start_price - 1",
        "risk": "sample_volatility; max_drawdown; data-based financial flags",
        "capm": "E(Ri) = Rf + beta * market_risk_premium",
        "news": "review sourced, dated event annotations",
    }
    return {
        "version": "2.0",
        "schema_version": "1.0",
        "schema_status": "proposed_pending_team_agreement",
        "minimum_peers": 3,
        "minimum_peers_rationale": (
            "Design choice for comparison coverage; not an investment threshold."
        ),
        "required_margin": None,
        "threshold_rationale": None,
        "modules": {
            key: {"enabled": True, "formula": formula}
            for key, formula in formulas.items()
        },
        "theory_sources": [
            {
                "id": "value",
                "title": "Graham and Dodd, Security Analysis (1934)",
                "pages": None,
                "verification": "Edition-specific pages pending",
                "url": (
                    "https://www.mheducation.com/highered/mhp/product/"
                    "security-analysis-seventh-edition.html"
                ),
            },
            {
                "id": "valuation",
                "title": "Aswath Damodaran, Valuation teaching materials",
                "url": (
                    "https://pages.stern.nyu.edu/~adamodar/"
                    "New_Home_Page/valuation/val.htm"
                ),
            },
            {
                "id": "momentum",
                "title": "Jegadeesh and Titman (1993)",
                "pages": "65-91; sample p.67; portfolio construction p.68",
                "url": "https://doi.org/10.1111/j.1540-6261.1993.tb04702.x",
            },
            {
                "id": "capm",
                "title": "Sharpe (1964); Lintner (1965)",
                "pages": "Sharpe 425-442; Lintner 13-37",
                "url": "https://doi.org/10.1111/j.1540-6261.1964.tb02865.x",
                "supporting_url": "https://www.aea.ru/data/pdf/lintner1965.pdf",
            },
            {
                "id": "portfolio",
                "title": "Markowitz (1952), Portfolio Selection",
                "pages": "77-91",
                "url": "https://doi.org/10.1111/j.1540-6261.1952.tb01525.x",
            },
            {
                "id": "emh",
                "title": "Fama (1970), Efficient Capital Markets",
                "pages": "383-417",
                "verification": "Detailed full-text review pending",
                "url": "https://doi.org/10.1111/j.1540-6261.1970.tb00518.x",
            },
        ],
    }


class Engine:
    def __init__(self, payload, config):
        self.payload = payload
        self.config = config
        self.sources = {}
        self.evidence = {}
        self.used = set()
        self.results = []
        self.warnings = []
        self.as_of = day(payload["as_of"])

    def lookup(self, path):
        value = self.payload
        for key in path.split("."):
            if value is None:
                raise MissingData(f"Thiếu {path}.")
            if isinstance(value, list):
                try:
                    value = value[int(key)]
                except (ValueError, IndexError):
                    raise MissingData(f"Thiếu {path}.")
            elif isinstance(value, dict):
                value = value.get(key)
            else:
                raise ContractError(f"Sai cấu trúc tại {path}.")
        if value is None:
            raise MissingData(f"Thiếu {path}.")
        return value

    def validate_sources(self, node, path=""):
        if isinstance(node, list):
            for index, item in enumerate(node):
                self.validate_sources(item, f"{path}.{index}")
            return
        if not isinstance(node, dict):
            return

        if "value" in node:
            value = node["value"]
            if value is not None:
                check(
                    type(value) in (str, bool) or numeric(value),
                    f"{path}: value không hợp lệ.",
                )
                source = node.get("source")
                check(isinstance(source, str), f"{path}: thiếu source.")
                parsed = urlsplit(source)
                check(
                    parsed.scheme in ("http", "https") and parsed.hostname,
                    f"{path}: source phải là URL.",
                )
                if not self.payload["is_demo"]:
                    host = parsed.hostname.lower()
                    check(
                        host not in ("example.com", "example.org", "example.net"),
                        f"{path}: không dùng URL minh họa cho dữ liệu thật.",
                    )
                for field in ("period", "unit"):
                    check(
                        isinstance(node.get(field), str)
                        and node[field].strip(),
                        f"{path}: thiếu {field}.",
                    )
                check(
                    day(node.get("published_at")) <= self.as_of,
                    f"{path}: nguồn công bố sau ngày chốt.",
                )
                check(
                    day(node.get("observed_at")) <= self.as_of,
                    f"{path}: dữ liệu vượt ngày chốt.",
                )
                self.evidence[path] = copy.deepcopy(node)
                self.sources[path] = {
                    "ref_id": path,
                    "url": source,
                    "period": node["period"],
                    "published_at": node["published_at"],
                    "observed_at": node["observed_at"],
                    "unit": node["unit"],
                }

        for key, value in node.items():
            if isinstance(value, (dict, list)):
                child = f"{path}.{key}" if path else key
                self.validate_sources(value, child)

    def fact(self, path, unit, kind="number"):
        item = self.lookup(path)
        check(isinstance(item, dict) and "value" in item,
              f"{path}: cần object số liệu.")
        value = item["value"]
        if value is None:
            raise MissingData(f"{path} = null.")
        check(item.get("unit") == unit, f"{path}: cần đơn vị {unit}.")
        if kind == "number":
            check(numeric(value), f"{path}: cần số hữu hạn.")
        elif kind == "text":
            check(isinstance(value, str) and value.strip(),
                  f"{path}: cần chuỗi không rỗng.")
        elif kind == "boolean":
            check(type(value) is bool, f"{path}: cần boolean.")
        self.used.add(path)
        return value

    def compatible(self, paths, same_date=False):
        items = [self.lookup(path) for path in paths]
        key = "observed_at" if same_date else "period"
        check(len({item[key] for item in items}) == 1,
              f"Các đầu vào không cùng {key}: {paths}")

    def run_module(self, name, method):
        self.used = set()
        if not self.config["modules"][name]["enabled"]:
            self.results.append({
                "id": name, "status": "not_applied",
                "values": None, "evidence_refs": [],
                "explanation": "Module bị tắt theo cấu hình."
            })
            return
        try:
            values = method()
            result = {
                "id": name,
                "status": "evaluated",
                "values": values,
                "evidence_refs": sorted(self.used),
                "explanation": "Đã tính từ đầu vào; cần kiểm chứng nguồn thực tế.",
            }
        except MissingData as exc:
            result = {
                "id": name,
                "status": "insufficient_data",
                "values": None,
                "evidence_refs": sorted(self.used),
                "explanation": str(exc),
            }
        self.results.append(result)

    def drivers(self, name):
        items = self.lookup(f"{name}.drivers")
        check(isinstance(items, list), f"{name}.drivers phải là list.")
        if not items:
            raise MissingData(f"Chưa có động lực phân tích {name}.")
        output = []
        for index, item in enumerate(items):
            base = f"{name}.drivers.{index}"
            check(isinstance(item, dict), f"{base}: cần object.")
            current_item = self.lookup(base + ".current")
            previous_item = self.lookup(base + ".previous")
            unit = current_item.get("unit")
            check(unit in ("fraction", "VND", "index"),
                  f"{base}: đơn vị driver chưa hỗ trợ.")
            current = self.fact(base + ".current", unit)
            previous = self.fact(base + ".previous", unit)
            check(
                day(previous_item["observed_at"])
                < day(current_item["observed_at"]),
                f"{base}: kỳ trước phải có ngày trước kỳ hiện tại.",
            )
            effect = self.fact(base + ".effect_if_rises", "text", "text")
            mechanism = self.fact(base + ".mechanism", "text", "text")
            check(effect in ("tailwind", "headwind", "mixed"),
                  f"{base}: effect_if_rises không hợp lệ.")
            change = current - previous
            direction = "up" if change > 0 else "down" if change < 0 else "flat"
            if direction == "flat":
                actual_effect = "neutral"
            elif direction == "down" and effect != "mixed":
                actual_effect = {
                    "tailwind": "headwind", "headwind": "tailwind"
                }[effect]
            else:
                actual_effect = effect
            output.append({
                "name": item.get("name"),
                "change": change,
                "change_unit": unit,
                "direction": direction,
                "conditional_effect": actual_effect,
                "mechanism": mechanism,
            })
        return {
            "drivers": output,
            "limitation": (
                "Tác động có điều kiện theo cơ chế đầu vào; "
                "chưa phải ước lượng nhân quả hoặc dự báo lợi nhuận."
            ),
        }

    def industry(self):
        current = self.fact("industry.revenue_current", "VND")
        previous = self.fact("industry.revenue_previous", "VND")
        a = self.lookup("industry.revenue_current")
        b = self.lookup("industry.revenue_previous")
        check(day(b["observed_at"]) < day(a["observed_at"]),
              "Sai thứ tự kỳ ngành.")
        check(
            self.lookup("industry.comparable_periods") is True,
            "Cần xác nhận kỳ ngành có cùng độ dài và phạm vi thống kê.",
        )
        growth = ratio(current, previous) - 1
        output = {"industry_revenue_growth": growth}
        try:
            company_growth = self.financial_growth("revenue")
            self.compatible([
                "industry.revenue_current",
                "company.financial.current.revenue",
            ])
            output["company_growth_minus_industry"] = company_growth - growth
        except MissingData:
            output["company_growth_minus_industry"] = None
        if self.lookup("industry").get("drivers"):
            output["outlook"] = self.drivers("industry")
        return output

    def financial_growth(self, field):
        current_path = f"company.financial.current.{field}"
        previous_path = f"company.financial.previous.{field}"
        current = self.fact(current_path, "VND")
        previous = self.fact(previous_path, "VND")
        return ratio(current, previous) - 1

    def fundamental(self):
        finance = self.lookup("company.financial")
        check(finance.get("period_type") in ("annual", "TTM"),
              "V2 nhận BCTC năm hoặc TTM.")
        check(finance.get("comparable_periods") is True,
              "Cần xác nhận kỳ BCTC tương thích.")
        prefix = "company.financial"
        current = lambda key: self.fact(f"{prefix}.current.{key}", "VND")
        previous = lambda key: self.fact(f"{prefix}.previous.{key}", "VND")

        # Kiểm các chỉ tiêu trong mỗi kỳ có cùng period.
        for group in ("current", "previous"):
            block = finance.get(group)
            check(isinstance(block, dict), f"Thiếu financial.{group}.")
            items = [
                value for value in block.values()
                if isinstance(value, dict) and value.get("value") is not None
            ]
            check(len({item["period"] for item in items}) <= 1,
                  f"Trộn kỳ BCTC trong {group}.")
        a = self.lookup(f"{prefix}.current.revenue")
        b = self.lookup(f"{prefix}.previous.revenue")
        check(day(b["observed_at"]) < day(a["observed_at"]),
              "Sai thứ tự kỳ BCTC.")

        calculations = {
            "revenue_growth": lambda: self.financial_growth("revenue"),
            "profit_growth": lambda: self.financial_growth("net_income"),
            "net_margin": lambda: ratio(current("net_income"), current("revenue")),
            "roe": lambda: ratio(
                current("net_income"), (current("equity") + previous("equity")) / 2
            ),
            "roa": lambda: ratio(
                current("net_income"), (current("assets") + previous("assets")) / 2
            ),
            "debt_to_equity": lambda: ratio(current("debt"), current("equity")),
            "current_ratio": lambda: ratio(
                current("current_assets"), current("current_liabilities")
            ),
            "interest_coverage": lambda: ratio(
                current("ebit"), current("interest_expense")
            ),
            "cfo_to_profit": lambda: ratio(current("cfo"), current("net_income")),
            "cash_after_capex": lambda: current("cfo") - current("capex"),
        }
        values = {}
        for name, calculate in calculations.items():
            try:
                values[name] = calculate()
            except MissingData as exc:
                values[name] = None
                self.warnings.append(f"fundamental.{name}: {exc}")
        if not any(value is not None for value in values.values()):
            raise MissingData("Không tính được chỉ tiêu tài chính.")
        values["limitations"] = (
            "ROE/ROA dùng số dư bình quân hai kỳ; "
            "cash_after_capex không mặc nhiên là FCFF hoặc FCFE. "
            "Các tỷ số chung không thay thế phân tích đặc thù ngân hàng."
        )
        return values

    def value(self):
        price = self.fact("company.price", "VND/share")
        low = self.fact("company.valuation.low", "VND/share")
        high = self.fact("company.valuation.high", "VND/share")
        check(price > 0 and 0 < low <= high, "Khoảng định giá không hợp lệ.")
        valuation = self.lookup("company.valuation")
        check(valuation.get("method") in ("DCF", "asset_based"),
              "Phương pháp định giá chưa hỗ trợ.")
        check(isinstance(valuation.get("assumptions"), dict)
              and valuation["assumptions"], "Thiếu giả định định giá.")
        limitations = valuation.get("limitations")
        check(isinstance(limitations, list) and limitations
              and all(isinstance(x, str) and x.strip() for x in limitations),
              "Thiếu giới hạn định giá.")
        self.compatible([
            "company.price", "company.valuation.low", "company.valuation.high"
        ], same_date=True)
        margin = 1 - price / low
        required = self.config["required_margin"]
        if required is not None:
            check(numeric(required) and 0 <= required < 1,
                  "Sai ngưỡng biên an toàn.")
            check(isinstance(self.config["threshold_rationale"], str)
                  and self.config["threshold_rationale"].strip(),
                  "Ngưỡng cần lý do công khai.")
        self.evidence["company.valuation.methodology"] = {
            "method": valuation["method"],
            "assumptions": valuation["assumptions"],
            "limitations": limitations,
        }
        self.used.add("company.valuation.methodology")
        return {
            "margin_conservative": margin,
            "margin_optimistic": 1 - price / high,
            "required_margin": required,
            "meets_policy": None if required is None else margin >= required,
            "limitations": limitations,
        }

    def relative(self):
        price = self.fact("company.price", "VND/share")
        check(price > 0, "Giá phải dương.")
        company = self.lookup("company")
        business_type = company.get("business_type")
        check(business_type in ("nonfinancial", "bank", "securities"),
              "Cần business_type rõ ràng.")
        basis = company.get("accounting_basis")
        check(isinstance(basis, str) and basis.strip(),
              "Thiếu accounting_basis.")

        peers = self.lookup("industry.peers")
        check(isinstance(peers, list), "industry.peers phải là list.")
        multiple_lists = {"PE": [], "PB": []}
        excluded = []
        seen = {self.payload["ticker"]}

        # EPS phải là EPS TTM; BVPS là số liệu tại một thời điểm.
        definitions = (
            ("PE", "eps_ttm", business_type == "nonfinancial"),
            ("PB", "bvps", True),
        )
        targets = {}
        for method, field, applicable in definitions:
            try:
                denominator = self.fact(f"company.{field}", "VND/share")
                if applicable and denominator > 0:
                    targets[method] = denominator
            except MissingData:
                pass
        if "PE" in targets:
            normalized = self.fact(
                "company.earnings_normalized", "boolean", "boolean"
            )
            if not normalized:
                targets.pop("PE")

        target_date = self.lookup("company.price")["observed_at"]
        for index, peer in enumerate(peers):
            check(isinstance(peer, dict), "Mỗi peer phải là object.")
            ticker = peer.get("ticker")
            check(isinstance(ticker, str) and ticker.strip(), "Peer thiếu ticker.")
            check(ticker not in seen, "Peer trùng hoặc chứa chính mã đang phân tích.")
            seen.add(ticker)
            base = f"industry.peers.{index}"
            if (
                peer.get("sector") != self.payload["sector"]
                or peer.get("accounting_basis") != basis
                or peer.get("business_type") != business_type
            ):
                excluded.append({"ticker": ticker, "reason": "Không cùng nhóm."})
                continue

            self.fact(base + ".comparability_note", "text", "text")
            # Note phải giải thích cả khác biệt tăng trưởng và rủi ro.
            peer_price = self.fact(base + ".price", "VND/share")
            check(peer_price > 0, "Giá peer phải dương.")
            if self.lookup(base + ".price")["observed_at"] != target_date:
                excluded.append({"ticker": ticker, "reason": "Giá khác ngày."})
                continue

            for method, field, _ in definitions:
                if method not in targets:
                    continue
                try:
                    denominator = self.fact(base + "." + field, "VND/share")
                    self.compatible(["company." + field, base + "." + field])
                    if denominator <= 0:
                        excluded.append({
                            "ticker": ticker, "method": method,
                            "reason": "Mẫu số không dương.",
                        })
                        continue
                    if method == "PE":
                        if not self.fact(
                            base + ".earnings_normalized", "boolean", "boolean"
                        ):
                            continue
                    multiple_lists[method].append({
                        "ticker": ticker, "multiple": peer_price / denominator
                    })
                except MissingData:
                    continue

        minimum = self.config["minimum_peers"]
        check(type(minimum) is int and minimum >= 2, "Sai minimum_peers.")
        estimates = {}
        for method, members in multiple_lists.items():
            if len(members) < minimum:
                continue
            median = statistics.median(x["multiple"] for x in members)
            reference = targets[method] * median
            estimates[method] = {
                "company_multiple": price / targets[method],
                "peer_median": median,
                "relative_price_reference": reference,
                "discount_to_reference": 1 - price / reference,
                "peers": members,
            }
        if not estimates:
            raise MissingData("Không đủ peer tương thích để định giá tương đối.")
        return {
            "estimates": estimates,
            "excluded_peers": excluded,
            "limitation": (
                "Mức tham chiếu tương đối không phải giá trị nội tại; "
                "khả năng so sánh cần được người phân tích kiểm chứng."
            ),
        }

    def series(self, path):
        block = self.lookup(path)
        check(isinstance(block, dict), f"{path}: cần object.")
        points = block.get("points")
        check(isinstance(points, list), f"{path}.points phải là list.")
        unit = block.get("unit")
        check(unit in ("VND/share", "index"), f"{path}: sai đơn vị.")
        if block.get("adjusted") is not True:
            raise MissingData(f"{path}: chưa xác nhận dữ liệu điều chỉnh.")
        values = {}
        for index, point in enumerate(points):
            base = f"{path}.points.{index}"
            value = self.fact(base, unit)
            check(value > 0, f"{base}: giá/chỉ số phải dương.")
            observed = day(point["observed_at"])
            check(observed not in values, f"{path}: trùng ngày.")
            values[observed] = value
        if len(values) < 3:
            raise MissingData(f"{path}: cần ít nhất 3 điểm.")
        return sorted(values.items()), block

    def momentum(self):
        points, block = self.series("company.monthly_prices")
        check(block.get("frequency") == "month_end", "Cần giá cuối tháng.")
        indexed = {}
        for observed, value in points:
            month = observed.year * 12 + observed.month - 1
            check(month not in indexed, "Trùng tháng momentum.")
            indexed[month] = value
        end = self.as_of.year * 12 + self.as_of.month - 2
        months = list(range(end - 6, end + 1))
        if not all(month in indexed for month in months):
            raise MissingData("Cần 7 tháng hoàn chỉnh liên tiếp.")
        return {
            "price_return_6m": indexed[end] / indexed[end - 6] - 1,
            "limitation": (
                "Mô tả một mã; không tái lập danh mục momentum "
                "và không chứng minh lợi nhuận tương lai."
            ),
        }

    def risk(self):
        points, block = self.series("company.history")
        check(block.get("frequency") == "daily", "Risk v2 cần chuỗi daily.")
        periods = block.get("periods_per_year")
        check(type(periods) is int and periods > 0,
              "Cần quy ước periods_per_year.")
        returns = [
            points[i][1] / points[i - 1][1] - 1
            for i in range(1, len(points))
        ]
        peak = points[0][1]
        drawdowns = []
        for _, value in points:
            peak = max(peak, value)
            drawdowns.append(value / peak - 1)
        flags = []
        for field, condition, message in (
            ("net_income", lambda x: x < 0, "Doanh nghiệp đang lỗ."),
            ("cfo", lambda x: x < 0, "Dòng tiền kinh doanh âm."),
            ("equity", lambda x: x <= 0, "Vốn chủ sở hữu không dương."),
        ):
            try:
                value = self.fact(f"company.financial.current.{field}", "VND")
                if condition(value):
                    flags.append(message)
            except MissingData:
                self.warnings.append(f"Chưa đánh giá rủi ro tài chính: {field}.")
        return {
            "sample_return_count": len(returns),
            "sample_start": points[0][0].isoformat(),
            "sample_end": points[-1][0].isoformat(),
            "volatility_annualized": statistics.stdev(returns) * math.sqrt(periods),
            "max_drawdown": min(drawdowns),
            "financial_flags": flags,
            "position_limit": None,
            "limitation": (
                "Ước lượng trên mẫu được cung cấp; chưa đo rủi ro danh mục, "
                "thanh khoản hoặc đặt tỷ trọng/stop-loss theo khẩu vị người dùng."
            ),
        }

    def capm(self):
        stock, stock_block = self.series("company.history")
        market, market_block = self.series("market.benchmark")
        if (
            stock_block.get("return_basis") != "total_return"
            or market_block.get("return_basis") != "total_return"
        ):
            raise MissingData("CAPM cần hai chuỗi total_return tương thích.")
        for key in ("frequency", "periods_per_year", "calendar", "currency"):
            check(
                stock_block.get(key) is not None
                and stock_block.get(key) == market_block.get(key),
                f"CAPM: hai chuỗi khác {key}.",
            )
        if [d for d, _ in stock] != [d for d, _ in market]:
            raise MissingData("CAPM cần ngày quan sát đồng bộ; không tự điền giá.")
        check(stock_block.get("frequency") == "daily",
              "CAPM v2 nhận tần suất daily.")
        rf = self.fact("market.risk_free_annual", "fraction")
        premium = self.fact("market.market_risk_premium_annual", "fraction")
        self.fact("market.benchmark_name", "text", "text")
        check(rf > -1, "Lãi suất phi rủi ro không hợp lệ.")
        periods = stock_block["periods_per_year"]
        check(type(periods) is int and periods > 0, "Sai periods_per_year.")
        daily_rf = (1 + rf) ** (1 / periods) - 1
        x = [
            market[i][1] / market[i - 1][1] - 1 - daily_rf
            for i in range(1, len(market))
        ]
        y = [
            stock[i][1] / stock[i - 1][1] - 1 - daily_rf
            for i in range(1, len(stock))
        ]
        mean_x, mean_y = statistics.mean(x), statistics.mean(y)
        denominator = sum((v - mean_x) ** 2 for v in x)
        if denominator == 0:
            raise MissingData("Benchmark không có phương sai để ước lượng beta.")
        beta = sum(
            (a - mean_x) * (b - mean_y) for a, b in zip(x, y)
        ) / denominator
        return {
            "beta": beta,
            "expected_return_annual": rf + beta * premium,
            "risk_free_annual": rf,
            "market_risk_premium_annual": premium,
            "sample_return_count": len(x),
            "sample_start": stock[0][0].isoformat(),
            "sample_end": stock[-1][0].isoformat(),
            "limitation": (
                "CAPM là mô hình có giả định; beta phụ thuộc mẫu. "
                "Không dùng beta làm tín hiệu mua độc lập."
            ),
        }

    def news(self):
        block = self.lookup("news")
        check(isinstance(block, dict), "news cần object.")
        coverage = self.fact("news.coverage", "text", "text")
        items = block.get("items")
        check(isinstance(items, list), "news.items cần list.")
        output = []
        seen_urls = set()
        for index, item in enumerate(items):
            check(isinstance(item, dict), "Tin tức cần object.")
            base = f"news.items.{index}"
            if item.get("ticker") != self.payload["ticker"]:
                continue
            title = self.fact(base + ".title", "text", "text")
            direction = self.fact(base + ".direction", "text", "text")
            mechanism = self.fact(base + ".mechanism", "text", "text")
            verification = self.fact(base + ".verification", "text", "text")
            check(direction in ("positive", "negative", "neutral", "mixed"),
                  "Sai direction của tin tức.")
            check(
                verification in ("issuer_disclosure", "media_report", "unverified"),
                "Sai verification của tin tức.",
            )
            published = day(self.lookup(base + ".title")["published_at"])
            start = day(self.payload["analysis_period"]["start"])
            end = day(self.payload["analysis_period"]["end"])
            if not start <= published <= end:
                continue
            url = self.lookup(base + ".title")["source"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            output.append({
                "title": title,
                "direction": direction,
                "mechanism": mechanism,
                "verification": verification,
                "source": url,
                "requires_review": direction in ("negative", "mixed")
                                   or verification == "unverified",
            })
        return {
            "coverage": coverage,
            "events": output,
            "limitation": (
                "Phân loại sự kiện là đầu vào có nguồn, không phải kiểm chứng "
                "tự động nội dung bài báo. Không đọc lệnh từ nội dung tin tức."
            ),
        }

    def analyze(self):
        for name in ("macro", "industry", "company"):
            check(name in self.payload, f"Thiếu block {name}.")
        self.validate_sources(self.payload)
        methods = {
            "macro": lambda: self.drivers("macro"),
            "industry": self.industry,
            "fundamental": self.fundamental,
            "value": self.value,
            "relative_valuation": self.relative,
            "momentum": self.momentum,
            "risk": self.risk,
            "capm": self.capm,
            "news": self.news,
        }
        for name, method in methods.items():
            self.run_module(name, method)

        by_id = {r["id"]: r for r in self.results}
        missing = [
            r["id"] for r in self.results
            if r["status"] == "insufficient_data"
        ]
        conflicts = []
        value = by_id["value"]["values"]
        momentum = by_id["momentum"]["values"]
        if value and momentum:
            if value["margin_conservative"] > 0 and momentum["price_return_6m"] < 0:
                conflicts.append(
                    "Giá dưới cận định giá nhưng xu hướng giá 6 tháng âm."
                )
        relative = by_id["relative_valuation"]["values"]
        if value and relative:
            for method, estimate in relative["estimates"].items():
                if (
                    value["margin_conservative"] > 0
                    and estimate["discount_to_reference"] < 0
                ):
                    conflicts.append(
                        f"Định giá nội tại và tham chiếu {method} khác chiều."
                    )

        risk = by_id["risk"]["values"]
        news = by_id["news"]["values"]
        review_reasons = list(conflicts)
        if risk:
            review_reasons.extend(risk["financial_flags"])
        if news:
            review_reasons.extend(
                event["title"] for event in news["events"]
                if event["requires_review"]
            )

        self.warnings.extend([
            "Không khẳng định alpha; chưa kiểm định ngoài mẫu và chi phí giao dịch.",
            "Chưa kiểm chứng dữ liệu thật với tài liệu gốc.",
            "Không tối ưu danh mục trong phạm vi phân tích một mã.",
            "Chưa đặt giới hạn vị thế vì thiếu danh mục và khẩu vị rủi ro.",
            "Trang sách Graham/Dodd và đối chiếu chi tiết Fama còn cần bổ sung.",
            "Schema cần được nhóm thống nhất trước khi tích hợp.",
        ])
        self.warnings.extend(
            f"{r['id']}: {r['explanation']}" for r in self.results
            if r["status"] != "evaluated"
        )
        if self.payload["is_demo"]:
            status = "demo_only"
        elif missing:
            status = "insufficient_data"
        else:
            status = "requires_review"

        return {
            "status": status,
            "data": {
                "module_version": "2.0",
                "is_demo": self.payload["is_demo"],
                "validation": {
                    "contract": "passed",
                    "real_data_verified": False,
                    "schema_status": self.config["schema_status"],
                },
                "theory_sources": self.config["theory_sources"],
                "rules": self.results,
                "evidence_refs": self.evidence,
                "conclusion": {
                    "status": status,
                    "recommendation": None,
                    "missing_modules": missing,
                    "conflicting_signals": conflicts,
                    "review_reasons": review_reasons,
                    "explanation": (
                        "Đánh giá theo từng trụ cột; không gộp thành điểm mua "
                        "bằng trọng số tùy ý. Xem chỉ tiêu, nguồn và giới hạn."
                    ),
                },
                "risks": {
                    "market_and_financial": risk,
                    "event_risks": (
                        [event for event in news["events"] if event["requires_review"]]
                        if news else None
                    ),
                    "methodological": [
                        "Sai lệch hoặc thiếu dữ liệu.",
                        "Sai giả định định giá.",
                        "Nhóm so sánh không tương thích.",
                        "Ước lượng beta/biến động phụ thuộc mẫu.",
                    ],
                },
            },
            "sources": list(self.sources.values()),
            "warnings": list(dict.fromkeys(self.warnings)),
            "errors": [],
        }


def evaluate(payload, config):
    metadata_keys = (
        "run_id", "ticker", "exchange", "sector", "as_of",
        "analysis_period", "investment_horizon_months"
    )
    metadata = payload if isinstance(payload, dict) else {}
    output = {
        "schema_version": "1.0",
        **{key: copy.deepcopy(metadata.get(key)) for key in metadata_keys},
        "status": "error",
        "data": None,
        "sources": [],
        "warnings": [],
        "errors": [],
    }
    try:
        check(isinstance(payload, dict), "Input phải là object.")
        check(payload.get("schema_version") == "1.0", "Sai schema_version.")
        for key in ("run_id", "ticker", "exchange", "sector"):
            check(
                isinstance(payload.get(key), str) and payload[key].strip(),
                f"Thiếu {key}.",
            )
        check(payload["exchange"] in ("HOSE", "HNX", "UPCOM"), "Sai exchange.")
        check(type(payload.get("is_demo")) is bool, "is_demo phải là boolean.")
        as_of = day(payload.get("as_of"))
        period = payload.get("analysis_period")
        check(isinstance(period, dict), "Thiếu analysis_period.")
        check(day(period.get("start")) <= day(period.get("end")) <= as_of,
              "Sai khoảng phân tích.")
        horizon = payload.get("investment_horizon_months")
        check(type(horizon) is int and horizon > 0, "Sai thời hạn đầu tư.")
        output.update(Engine(payload, config).analyze())
    except (ContractError, KeyError, TypeError) as exc:
        output["errors"] = [{"code": "CONTRACT_ERROR", "message": str(exc)}]
    return output


def demo_input():
    """Dữ liệu tổng hợp kiểm thử; không phải dữ liệu của một doanh nghiệp thật."""
    def fact(value, unit, period="2026-09-30", observed=None, published=None):
        observed = observed or period
        return {
            "value": value, "unit": unit, "period": period,
            "source": "https://example.com/synthetic-test-data",
            "observed_at": observed,
            "published_at": published or observed,
        }

    def text(value):
        return fact(value, "text")

    current = {
        "revenue": 1200, "net_income": 120, "equity": 600,
        "assets": 1000, "debt": 180, "current_assets": 400,
        "current_liabilities": 200, "ebit": 160,
        "interest_expense": 20, "cfo": 140, "capex": 40,
    }
    previous = {
        "revenue": 1000, "net_income": 100,
        "equity": 500, "assets": 900,
    }

    peers = []
    for index, price in enumerate((100, 110, 120)):
        peers.append({
            "ticker": f"PEER{index + 1}",
            "sector": "Demo sector",
            "business_type": "nonfinancial",
            "accounting_basis": "consolidated_VAS",
            "comparability_note": text(
                "Synthetic peers with matched growth and risk assumptions."
            ),
            "price": fact(price, "VND/share", "2026-10-09"),
            "eps_ttm": fact(10, "VND/share"),
            "bvps": fact(50, "VND/share"),
            "earnings_normalized": fact(True, "boolean"),
        })

    stock_points, market_points = [], []
    stock_value = market_value = 100.0
    start = date(2026, 7, 1)
    index = 0
    for offset in range(101):
        observed = start + timedelta(days=offset)
        if observed > date(2026, 10, 9) or observed.weekday() >= 5:
            continue
        market_return = (0.002, -0.001, 0.003, -0.002)[index % 4]
        stock_value *= 1 + 1.2 * market_return
        market_value *= 1 + market_return
        ds = observed.isoformat()
        stock_points.append(fact(stock_value, "index", ds))
        market_points.append(fact(market_value, "index", ds))
        index += 1

    def history(points):
        return {
            "unit": "index", "adjusted": True,
            "return_basis": "total_return", "frequency": "daily",
            "periods_per_year": 252, "calendar": "DEMO_WEEKDAYS",
            "currency": "VND", "points": points,
        }

    monthly = []
    for index, month in enumerate(range(3, 10)):
        ds = date(2026, month, calendar.monthrange(2026, month)[1]).isoformat()
        monthly.append(fact(100 + index, "VND/share", ds))

    return {
        "schema_version": "1.0", "run_id": "synthetic-v2-001",
        "ticker": "TEST", "exchange": "HOSE", "sector": "Demo sector",
        "as_of": "2026-10-09",
        "analysis_period": {"start": "2025-01-01", "end": "2026-10-09"},
        "investment_horizon_months": 12, "is_demo": True,
        "macro": {
            "drivers": [{
                "name": "Demo borrowing rate",
                "current": fact(0.06, "fraction"),
                "previous": fact(0.07, "fraction", "2025-09-30"),
                "effect_if_rises": text("headwind"),
                "mechanism": text(
                    "Conditional assumption: higher rates raise financing costs."
                ),
            }]
        },
        "industry": {
            "revenue_current": fact(11000, "VND"),
            "revenue_previous": fact(10000, "VND", "2025-09-30"),
            "comparable_periods": True,
            "peers": peers,
        },
        "company": {
            "business_type": "nonfinancial",
            "accounting_basis": "consolidated_VAS",
            "price": fact(100, "VND/share", "2026-10-09"),
            "eps_ttm": fact(12, "VND/share"),
            "bvps": fact(60, "VND/share"),
            "earnings_normalized": fact(True, "boolean"),
            "valuation": {
                "method": "asset_based",
                "assumptions": {"note": "Synthetic scenario, not a real valuation."},
                "limitations": ["Synthetic test assumptions only."],
                "low": fact(125, "VND/share", "2026-10-09"),
                "high": fact(150, "VND/share", "2026-10-09"),
            },
            "financial": {
                "period_type": "TTM", "comparable_periods": True,
                "current": {k: fact(v, "VND") for k, v in current.items()},
                "previous": {
                    k: fact(v, "VND", "2025-09-30")
                    for k, v in previous.items()
                },
            },
            "monthly_prices": {
                "unit": "VND/share", "adjusted": True,
                "frequency": "month_end", "points": monthly,
            },
            "history": history(stock_points),
        },
        "market": {
            "benchmark": history(market_points),
            "benchmark_name": text("Synthetic benchmark"),
            "risk_free_annual": fact(0.04, "fraction"),
            "market_risk_premium_annual": fact(0.06, "fraction"),
        },
        "news": {
            "coverage": text("Synthetic event set for software testing."),
            "items": [{
                "ticker": "TEST",
                "title": text("Synthetic event requiring review"),
                "direction": text("negative"),
                "mechanism": text("Synthetic risk annotation, not real news."),
                "verification": text("unverified"),
            }],
        },
    }


def self_test():
    config = defaults()
    payload = demo_input()
    result = evaluate(payload, config)
    assert not result["errors"], result["errors"]
    assert result["status"] == "demo_only"
    rules = {r["id"]: r for r in result["data"]["rules"]}
    assert all(r["status"] == "evaluated" for r in rules.values()), rules
    assert math.isclose(rules["fundamental"]["values"]["revenue_growth"], 0.2)
    assert math.isclose(rules["fundamental"]["values"]["net_margin"], 0.1)
    assert math.isclose(rules["industry"]["values"]["industry_revenue_growth"], 0.1)
    assert math.isclose(rules["value"]["values"]["margin_conservative"], 0.2)
    pe = rules["relative_valuation"]["values"]["estimates"]["PE"]
    assert math.isclose(pe["relative_price_reference"], 132)
    assert math.isclose(rules["momentum"]["values"]["price_return_6m"], 0.06)
    assert math.isclose(rules["capm"]["values"]["beta"], 1.2, abs_tol=1e-9)
    assert result["data"]["conclusion"]["recommendation"] is None
    assert result["data"]["risks"]["event_risks"]

    for block in ("macro", "industry", "company"):
        case = copy.deepcopy(payload)
        case[block] = None
        output = evaluate(case, config)
        assert not output["errors"], output["errors"]
        assert any(r["status"] == "insufficient_data"
                   for r in output["data"]["rules"])

    case = copy.deepcopy(payload)
    case["company"]["price"]["published_at"] = "2026-10-10"
    assert evaluate(case, config)["status"] == "error"

    case = copy.deepcopy(payload)
    case["company"]["price"]["value"] = "100"
    assert evaluate(case, config)["status"] == "error"

    case = copy.deepcopy(payload)
    case["industry"]["peers"] = case["industry"]["peers"][:1]
    output = evaluate(case, config)
    rule = next(r for r in output["data"]["rules"]
                if r["id"] == "relative_valuation")
    assert rule["status"] == "insufficient_data"

    case = copy.deepcopy(payload)
    case["company"]["history"]["return_basis"] = "price_only"
    output = evaluate(case, config)
    rule = next(r for r in output["data"]["rules"] if r["id"] == "capm")
    assert rule["status"] == "insufficient_data"

    case = copy.deepcopy(payload)
    case["is_demo"] = False
    assert evaluate(case, config)["status"] == "error"

    assert {source["ref_id"] for source in result["sources"]} <= set(
        result["data"]["evidence_refs"]
    )
    print("V2 self-test passed.")


def read_json(path):
    def reject(token):
        raise ContractError(f"JSON không cho phép {token}.")
    return json.loads(
        Path(path).read_text(encoding="utf-8-sig"),
        parse_constant=reject,
    )


def write_json(path, content):
    Path(path).write_text(
        json.dumps(content, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--init"]:
        for filename, content in (
            ("strategy_rules_v2.json", defaults()),
            ("input_full_demo.json", demo_input()),
        ):
            path = ROOT / filename
            if path.exists():
                print(f"Giữ file hiện có: {filename}")
            else:
                write_json(path, content)
                print(f"Đã tạo: {filename}")
    elif args == ["--self-test"]:
        self_test()
    elif len(args) == 2:
        payload = None
        try:
            payload = read_json(args[0])
            config = read_json(ROOT / "strategy_rules_v2.json")
            result = evaluate(payload, config)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            metadata = payload if isinstance(payload, dict) else {}
            result = {
                "schema_version": "1.0",
                "run_id": metadata.get("run_id"),
                "ticker": metadata.get("ticker"),
                "as_of": metadata.get("as_of"),
                "status": "error", "data": None,
                "sources": [], "warnings": [],
                "errors": [{"code": "INPUT_OR_CONFIG_ERROR", "message": str(exc)}],
            }
        write_json(args[1], result)
        print(f"Đã tạo {args[1]}; status={result['status']}")
        raise SystemExit(1 if result["status"] == "error" else 0)
    else:
        raise SystemExit(
            "Dùng: --init | --self-test | INPUT.json OUTPUT.json"
        )