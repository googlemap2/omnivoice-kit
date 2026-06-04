"""Compatibility router kept during backend router split.

Workflow endpoints now live in focused modules under ``backend.app.routers``.
"""

from fastapi import APIRouter

router = APIRouter()
