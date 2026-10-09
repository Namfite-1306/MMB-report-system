"""Module Ngành (Industry Module) - Người 2 phụ trách.
Hệ thống phân tích cơ hội đầu tư cổ phiếu MMB.
"""

from industry.analyzer import analyze_industry, build_pending_industry_output
from industry.schema import validate_industry_output

__all__ = ["analyze_industry", "build_pending_industry_output", "validate_industry_output"]
