"""Pydantic models for the Sprint 3 routing endpoints."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ManualRouteRequest(BaseModel):
    client_id: UUID
    registration_id: UUID
    override_reason: str = Field(..., min_length=10, max_length=2000)


class AddClientRequest(BaseModel):
    pan: str = Field(..., pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]$")
    legal_name: str = Field(..., min_length=1, max_length=255)
    trade_name: str | None = None
    entity_type: str | None = None
    cin: str | None = None
    date_of_incorporation_or_birth: date | None = None
    industry: str | None = None
    auto_route_inbox_id: UUID | None = Field(
        default=None,
        description="If set, runs routing again for this inbox row after creating the client.",
    )


class AddRegistrationRequest(BaseModel):
    client_id: UUID
    registration_type: Literal["IT", "GST"]
    identifier_value: str
    state_code: str | None = Field(default=None, pattern=r"^[0-9]{2}$")
    state_name: str | None = None
    jurisdiction_office: str | None = None
    auto_route_inbox_id: UUID | None = None


class RejectInboxRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=2000)


class RoutingDecisionView(BaseModel):
    inbox_id: UUID
    routing_status: str
    canonical_pan: str | None = None
    matched_client_id: UUID | None = None
    matched_registration_id: UUID | None = None
    created_matter_id: UUID | None = None
    created_notice_id: UUID | None = None
    anomaly_details: dict[str, Any] | None = None
