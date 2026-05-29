from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Track(str, Enum):
    GTM = "gtm"
    FINANCE = "finance"
    SECURITY = "security"


class ImpactLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class InsightBrief(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    summary: str
    impact: ImpactLevel
    recommendations: List[str]
    track: Track
    timestamp: datetime = Field(default_factory=_utc_now)
    source_url: str = ""
    source_name: str = ""
    similarity_score: float = 0.0
    cross_track_links: List[str] = []
    raw_findings: str = ""


class WatchListItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    track: Track
    name: str
    description: str
    anomaly_threshold: float = 0.85
    active: bool = True


class SearchQuery(BaseModel):
    query: str
    track: Optional[Track] = None
    country: str = "US"
    num_results: int = 10


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str = ""
    published_date: Optional[str] = None


class CompetitorSignal(BaseModel):
    company: str
    url: str
    change_type: str
    description: str
    timestamp: datetime = Field(default_factory=_utc_now)
    impact: ImpactLevel = ImpactLevel.MEDIUM


class FinancialSignal(BaseModel):
    signal_type: str
    source: str
    title: str
    description: str
    impact_score: float
    timestamp: datetime = Field(default_factory=_utc_now)
    data: Dict[str, Any] = {}


class SecurityAlert(BaseModel):
    alert_type: str
    severity: ImpactLevel
    description: str
    affected_entities: List[str] = []
    action_required: bool = False
    timestamp: datetime = Field(default_factory=_utc_now)
    source_url: str = ""


class VoiceCommandRequest(BaseModel):
    audio_base64: str
    format: str = "wav"
    language: str = "en"


class VoiceCommandResponse(BaseModel):
    transcript: str
    command_type: str
    result: Optional[str] = None
    track_switched_to: Optional[Track] = None


class EngineStatus(BaseModel):
    running: bool
    watchlist_count: int
    insights_generated: int
    last_check: Optional[datetime] = None
    anomalies_detected: int
    next_check: Optional[datetime] = None
    active_agents: int = 0


class TriggerConfig(BaseModel):
    name: str
    webhook_url: str
    tracks: List[Track] = []
    impact_threshold: ImpactLevel = ImpactLevel.HIGH
    headers: Dict[str, str] = {}
    active: bool = True


class DemoScenarioRequest(BaseModel):
    scenario: str = "competitor_price_cut"


class GTMSearchRequest(BaseModel):
    competitor_url: Optional[str] = None
    query: Optional[str] = None
    signals: List[str] = ["pricing", "messaging", "hiring"]


class FinanceSearchRequest(BaseModel):
    query: Optional[str] = None
    signal_types: List[str] = ["pricing", "regulatory", "alt_data"]
    regions: List[str] = ["US", "EU"]


class SecuritySearchRequest(BaseModel):
    query: Optional[str] = None
    alert_types: List[str] = ["credential_leak", "brand_threat", "regulatory"]
    severity_filter: Optional[ImpactLevel] = None
