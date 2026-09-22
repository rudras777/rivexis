from __future__ import annotations
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ProviderMetadata(BaseModel):
    provider_id: str
    provider_name: str
    category: str
    data_types: list[str] = Field(default_factory=list)
    supported_chains: list[str] = Field(default_factory=list)
    supported_assets: list[str] = Field(default_factory=list)
    supported_engines: list[str] = Field(default_factory=list)
    authentication_type: str = "api_key"
    commercial_tier: str = "external"
    expected_freshness: str = "context-dependent"
    provider_priority: int = 100
    license_notes: str = "Review commercial terms before production use."
    enabled: bool = False
    env_keys: list[str] = Field(default_factory=list)

class ProviderHealth(BaseModel):
    provider_id: str
    status: str
    configured: bool
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    detail: str | None = None
    latency_ms: float | None = None
    chain_id: int | None = None
    block_number: int | None = None
    error_code: str | None = None
