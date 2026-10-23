from __future__ import annotations

from pydantic import BaseModel, Field

from forvium.support_access.models import SupportAccessRequest, SupportConsent, SupportSession


class CreateRequestIn(BaseModel):
    organization_id: str
    reference_user_id: str
    reason: str = Field(max_length=4000)
    ticket_number: str = Field(max_length=32)
    duration_minutes: int | None = None
    scopes: list[str]
    mfa_code: str
    mode: str = "standard"
    incident_category: str | None = None  # wymagane dla mode="break_glass"


class BreakGlassDecisionIn(BaseModel):
    mfa_code: str | None = None
    note: str | None = Field(default=None, max_length=1000)


class BreakGlassReviewIn(BaseModel):
    notes: str = Field(max_length=4000)


class StartSessionIn(BaseModel):
    mfa_code: str
    duration_minutes: int | None = None


class ApproveIn(BaseModel):
    scopes: list[str] | None = None
    unit_ids: list[str] | None = None
    valid_hours: int | None = None
    note: str | None = Field(default=None, max_length=1000)


class RejectIn(BaseModel):
    note: str | None = Field(default=None, max_length=1000)


class StandingConsentIn(BaseModel):
    scopes: list[str]
    unit_ids: list[str] | None = None
    max_session_minutes: int = 15
    valid_days: int = 90
    allowed_platform_roles: list[str] | None = None
    note: str | None = Field(default=None, max_length=1000)
    mfa_code: str | None = None


class LaunchIn(BaseModel):
    code: str


def _iso(dt):
    return dt.isoformat() + "Z" if dt else None


def request_out(r: SupportAccessRequest) -> dict:
    return {
        "id": r.id,
        "mode": r.mode,
        "operator_id": r.operator_user_id,
        "organization_id": r.organization_id,
        "reference_user_id": r.reference_user_id,
        "ticket_number": r.ticket_number,
        "reason": r.reason,
        "scopes": r.requested_scopes,
        "duration_minutes": r.requested_duration_minutes,
        "access_level": r.access_level,
        "status": r.status,
        "created_at": _iso(r.created_at),
        "decision_deadline": _iso(r.decision_deadline),
        "decided_by_user_id": r.decided_by_user_id,
        "decided_at": _iso(r.decided_at),
        "decision_note": r.decision_note,
        "incident_category": r.incident_category,
        "review_completed_at": _iso(r.review_completed_at),
    }


def consent_out(c: SupportConsent | None) -> dict | None:
    if c is None:
        return None
    return {
        "id": c.id,
        "organization_id": c.organization_id,
        "scopes": c.scopes,
        "unit_ids": c.unit_ids,
        "access_level": c.access_level,
        "granted_by_user_id": c.granted_by_user_id,
        "granted_at": _iso(c.granted_at),
        "valid_until": _iso(c.valid_until),
        "revoked_at": _iso(c.revoked_at),
        "revoked_by_user_id": c.revoked_by_user_id,
        "basis": c.basis,
        "standing_consent_id": c.standing_consent_id,
    }


def session_out(s: SupportSession) -> dict:
    return {
        "id": s.id,
        "operator_id": s.operator_user_id,
        "organization_id": s.organization_id,
        "reference_user_id": s.reference_user_id,
        "consent_id": s.consent_id,
        "request_id": s.request_id,
        "ticket_number": s.ticket_number,
        "access_level": s.access_level,
        "permissions": s.permissions,
        "scopes": s.scopes,
        "unit_ids": s.unit_ids,
        "started_at": _iso(s.started_at),
        "expires_at": _iso(s.expires_at),
        "status": s.status,
        "ended_at": _iso(s.ended_at),
        "end_reason": s.end_reason,
    }
