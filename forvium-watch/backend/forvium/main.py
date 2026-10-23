"""Wspolny backend FastAPI dla admin.forvium.com i app.forvium.com."""

from __future__ import annotations

import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from forvium.audit.middleware import SupportAuditMiddleware
from forvium.audit.router import router as audit_admin
from forvium.security.router import router as security_admin
from forvium.support_access.recording import RecordingPolicy
from forvium.audit.service import AuditLog
from forvium.core.config import Settings, get_settings
from forvium.core.context import DomainError
from forvium.core.crypto import keyring_from_settings, set_keyring
from forvium.core.db import Database
from forvium.identity.router import admin_router as identity_admin
from forvium.identity.router import app_router as identity_app
from forvium.notifications.router import router as notifications_app
from forvium.notifications.service import NotificationEngine
from forvium.organizations.router import router as organizations_app
from forvium.platform_admin.router import router as platform_admin
from forvium.support_access.policy import DEFAULT_POLICY, SupportAccessPolicy
from forvium.support_access.router_admin import bg_router as break_glass_admin
from forvium.support_access.router_admin import router as support_admin
from forvium.support_access.router_app import router as support_app
from forvium.audit.chain import ChainedJsonlFile
from forvium.audit.export import sinks_from_settings
from forvium.jobs import start_jobs
from forvium.notifications.mailer import sender_from_settings
from forvium.security.anomalies import AnomalyPolicy
from forvium.identity.throttle import Throttle
from forvium.support_access.break_glass import BreakGlassPolicy


def create_app(settings: Settings | None = None, policy: SupportAccessPolicy | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        tasks = start_jobs(app) if settings.run_background_jobs else []
        yield
        for task in tasks:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    app = FastAPI(title="Forvium Watch API", version="1.0.0", lifespan=lifespan)

    # Bez poprawnego klucza danych aplikacja nie startuje (patrz core/crypto.py).
    set_keyring(keyring_from_settings(settings))
    db = Database(settings.database_url)
    if settings.auto_create_schema:
        db.create_all()
    app.state.settings = settings
    app.state.db = db
    break_glass_policy = BreakGlassPolicy.from_settings(settings)
    bg_sink = ChainedJsonlFile(settings.break_glass_audit_path, settings.audit_export_hmac_key.encode() or None) \
        if settings.break_glass_audit_path else None
    app.state.break_glass_policy = break_glass_policy
    app.state.audit = AuditLog(db.sessionmaker, break_glass_sink=bg_sink)
    app.state.notifications = NotificationEngine()
    app.state.email_sender = sender_from_settings(settings)
    app.state.throttle = Throttle(db.sessionmaker, app.state.audit)
    app.state.audit_sinks = sinks_from_settings(settings)
    app.state.anomaly_policy = AnomalyPolicy()
    app.state.recording_policy = RecordingPolicy()
    app.state.support_policy = policy or DEFAULT_POLICY

    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "message": exc.message})

    app.add_middleware(SupportAuditMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,  # tokeny w naglowku Authorization, nie w ciasteczkach
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    for router in (identity_app, organizations_app, support_app, notifications_app,
                   identity_admin, platform_admin, support_admin, break_glass_admin,
                   audit_admin, security_admin):
        app.include_router(router)

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    return app
