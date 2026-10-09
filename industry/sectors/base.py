"""Base definitions and data structures for sector data.
Cải thiện theo nhận xét phản biện ngày 09/10/2026:
- Bổ sung metadata thời gian cho từng peer: valuation_date, financial_period_end, period_type, statement_scope.
- Phân biệt rõ ràng not_applicable (ví dụ biên gộp của ngân hàng/chứng khoán) với missing.
- Chuẩn hóa thông tin kiểm chứng nguồn: verified_by, verification_date, verification_note.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PeerCompany:
    ticker: str
    name: str
    exchange: str
    market_cap: Optional[float]
    comparison_basis: str
    valuation_date: str = "2026-10-09"
    financial_period_end: str = "2025-12-31"
    period_type: str = "annual"
    statement_scope: str = "consolidated"
    not_applicable_metrics: List[str] = field(default_factory=list)
    metrics: Dict[str, Optional[float]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "exchange": self.exchange,
            "market_cap": self.market_cap,
            "comparison_basis": self.comparison_basis,
            "valuation_date": self.valuation_date,
            "financial_period_end": self.financial_period_end,
            "period_type": self.period_type,
            "statement_scope": self.statement_scope,
            "not_applicable_metrics": self.not_applicable_metrics,
            "metrics": self.metrics,
        }


@dataclass
class SectorMetric:
    metric_id: str
    name: str
    value: Optional[float]
    unit: str
    frequency: str
    period_start: str
    period_end: str
    source_refs: List[str]
    formula_id: Optional[str] = None
    sample_size: Optional[int] = None
    methodology_note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "metric_id": self.metric_id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "frequency": self.frequency,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "source_refs": self.source_refs,
            "formula_id": self.formula_id,
        }
        if self.sample_size is not None:
            res["sample_size"] = self.sample_size
        if self.methodology_note is not None:
            res["methodology_note"] = self.methodology_note
        return res


@dataclass
class SectorFinding:
    finding_id: str
    text: str
    evidence_refs: List[str]
    claim_type: str = "observation"  # observation | mechanism | forecast
    horizon: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "finding_id": self.finding_id,
            "text": self.text,
            "evidence_refs": self.evidence_refs,
            "claim_type": self.claim_type,
        }
        if self.horizon is not None:
            res["horizon"] = self.horizon
        return res


@dataclass
class SectorRisk:
    risk_id: str
    text: str
    evidence_refs: List[str]
    risk_category: str = "market"  # market | regulatory | raw_material | credit | liquidity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "text": self.text,
            "evidence_refs": self.evidence_refs,
            "risk_category": self.risk_category,
        }


@dataclass
class SectorSource:
    source_id: str
    title: str
    url: str
    published_at: Optional[str]
    retrieved_at: str
    locator: Optional[str]
    publication_date_verified: bool = True
    verified_by: str = "Nguoi_2"
    verification_date: str = "2026-10-09"
    verification_note: str = "Đối chiếu văn bản gốc / cổng công bố chính thức"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at,
            "retrieved_at": self.retrieved_at,
            "locator": self.locator,
            "publication_date_verified": self.publication_date_verified,
            "verified_by": self.verified_by,
            "verification_date": self.verification_date,
            "verification_note": self.verification_note,
        }


@dataclass
class SectorProfile:
    industry_code: str
    industry_name: str
    sector_cycle_stage: str
    peers: List[PeerCompany]
    metrics: List[SectorMetric]
    findings: List[SectorFinding]
    risks: List[SectorRisk]
    sources: List[SectorSource]
