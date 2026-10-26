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
from forvium.core.concurrency import ConcurrencyLimitMiddleware
from forvium.core.config import Settings, get_settings
from forvium.core.context import DomainError
from forvium.core.crypto import keyring_from_settings, set_keyring
from forvium.core.db import Database
from forvium.identity.router import admin_router as identity_admin
from forvium.identity.router import app_router as identity_app
from forvium.notifications.router import router as notifications_app
from forvium.notifications.service import NotificationEngine
from forvium.organizations.router import router as organizations_app
from forvium.platform_admin.manage import router as platform_manage
from forvium.platform_admin.router import router as platform_admin
from forvium.support_tickets.router import admin_router as tickets_admin
from forvium.support_tickets.router import app_router as tickets_app
from forvium.support_access.policy import DEFAULT_POLICY, SupportAccessPolicy
from forvium.support_access.router_admin import bg_router as break_glass_admin
from forvium.support_access.router_admin import router as support_admin
from forvium.support_access.router_app import router as support_app
from forvium.audit.chain import ChainedJsonlFile
from forvium.audit.export import sinks_from_settings
from forvium.jobs import start_jobs
from forvium.reports.router import admin_router as reports_admin
from forvium.reports.router import app_router as reports_app
from forvium.monitoring import install as install_monitoring
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
    db = Database(settings.database_url, settings.db_pool_size, settings.db_max_overflow, settings.db_aux_pool_size)
    if settings.auto_create_schema:
        db.create_all()
    app.state.settings = settings
    app.state.db = db
    break_glass_policy = BreakGlassPolicy.from_settings(settings)
    bg_sink = ChainedJsonlFile(settings.break_glass_audit_path, settings.audit_export_hmac_key.encode() or None) \
        if settings.break_glass_audit_path else None
    app.state.break_glass_policy = break_glass_policy
    app.state.audit = AuditLog(db.aux_sessionmaker, break_glass_sink=bg_sink)
    app.state.notifications = NotificationEngine()
    app.state.email_sender = sender_from_settings(settings)
    app.state.throttle = Throttle(db.aux_sessionmaker, app.state.audit)
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
        expose_headers=["Content-Disposition", "X-Content-SHA256", "X-Request-ID"],
    )

    for router in (identity_app, organizations_app, support_app, notifications_app,
                   identity_admin, platform_admin, platform_manage, tickets_admin, tickets_app,
                   support_admin, break_glass_admin,
                   audit_admin, security_admin, reports_app, reports_admin):
        app.include_router(router)

    # Najwyzej tyle zadan naraz, ile polaczen w glownej puli (core/concurrency.py).
    app.add_middleware(ConcurrencyLimitMiddleware, limit=db.max_connections)
    # Na koncu, wiec jako najbardziej zewnetrzne: identyfikator zadania obejmuje tez audyt i CORS.
    install_monitoring(app)

    @app.get("/healthz")
    async def healthz():  # bez puli watkow: odpowiada, dopoki dziala petla zdarzen
        return {"ok": True}

    return app
