from __future__ import annotations
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel


class ErrorPayload(BaseModel):
    code: str
    message: str


class Quote(BaseModel):
    symbol: str
    price: Optional[float] = None
    currency: Optional[str] = None
    open: Optional[float] = None
    dayHigh: Optional[float] = None
    dayLow: Optional[float] = None
    previousClose: Optional[float] = None
    ts: str
    source: str


class Bar(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjClose: Optional[float] = None


class HistoryResponse(BaseModel):
    symbol: str
    interval: str
    bars: List[Bar]


class OptionRow(BaseModel):
    contractSymbol: str
    strike: float
    lastPrice: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[float] = None
    openInterest: Optional[float] = None
    impliedVolatility: Optional[float] = None
    inTheMoney: Optional[bool] = None


class OptionsChainResponse(BaseModel):
    expiries: List[str]
    selectedExpiry: Optional[str]
    calls: List[OptionRow]
    puts: List[OptionRow]


class HealthzResponse(BaseModel):
    status: Literal["ok", "degraded", "fail"] = "ok"
    provider: str
    deep: bool = False
    provider_ok: Optional[bool] = None
    latency_ms: Optional[int] = None


class ConfigzResponse(BaseModel):
    provider: str
    config: Dict[str, Any]
