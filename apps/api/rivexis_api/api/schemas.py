from typing import Any
from pydantic import BaseModel, Field

class SignupRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)
    role: str = "Individual"
class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)
class RoleUpdate(BaseModel):
    role: str
class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
class OrganizationMemberAdd(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role: str = "ANALYST"
class OrganizationMemberClaimAccept(BaseModel):
    claim_token: str = Field(min_length=32, max_length=4096)
    role: str = "ANALYST"
class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    role: str = "Individual"
    organization_id: str | None = None
class AnalysisRequest(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)
    demo: bool = False
    workspace_id: str | None = None
class MonitorCreate(BaseModel):
    entity: str
    chain: str = "ethereum"
    rules: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    workspace_id: str | None = None

class HypernativeEvent(BaseModel):
    workspace_id: str
    monitor_id: str
    event_type: str = Field(min_length=1, max_length=120)
    severity: str = Field(default="unknown", max_length=24)
    affected_entity: str | None = Field(default=None, max_length=256)
    confidence: float | None = Field(default=None, ge=0, le=100)
    observed_at: str | None = Field(default=None, max_length=80)
    provider_payload: dict[str, Any] = Field(default_factory=dict)

class ReportRequest(BaseModel):
    decision_id: str
    format: str = "html"
class SavedAnalysisCreate(BaseModel):
    analysis_id: str
    title: str = Field(min_length=1, max_length=160)
class PortfolioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    wallets: list[str] = Field(default_factory=list)
    manual_positions: list[dict[str,Any]] = Field(default_factory=list)
    workspace_id: str | None = None


class ProtocolInvestigationCreate(BaseModel):
    workspace_id: str | None = None
    title: str = Field(min_length=2, max_length=160)
    input: dict[str, Any] = Field(default_factory=dict)
    notes: str = Field(default="", max_length=8000)

class ProtocolInvestigationUpdate(BaseModel):
    status: str | None = None
    disposition: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=8000)
