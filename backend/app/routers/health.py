"""Endpoint de health-check."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "maestro-backend",
        "env": settings.env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
