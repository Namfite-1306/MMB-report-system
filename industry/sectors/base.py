"""Base definitions and data structures for sector data."""
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
    metrics: Dict[str, Optional[float]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "exchange": self.exchange,
            "market_cap": self.market_cap,
            "comparison_basis": self.comparison_basis,
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

    def to_dict(self) -> Dict[str, Any]:
        return {
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


@dataclass
class SectorFinding:
    finding_id: str
    text: str
    evidence_refs: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "text": self.text,
            "evidence_refs": self.evidence_refs,
        }


@dataclass
class SectorRisk:
    risk_id: str
    text: str
    evidence_refs: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "text": self.text,
            "evidence_refs": self.evidence_refs,
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at,
            "retrieved_at": self.retrieved_at,
            "locator": self.locator,
            "publication_date_verified": self.publication_date_verified,
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
