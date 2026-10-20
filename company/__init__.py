"""Module doanh nghiệp của thành viên 3; không phụ thuộc macro/industry."""

def analyze_company(request, **kwargs):
    from .analyzer import analyze_company as analyze
    return analyze(request, **kwargs)

__all__ = ["analyze_company"]
