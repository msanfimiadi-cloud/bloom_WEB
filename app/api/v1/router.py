from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, bot_vk, clients, internal, partner, partners, privileges

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/runtime-info", tags=["runtime"])
def runtime_info() -> dict[str, str]:
    return {
        "app": "fed_women_club_WEB",
        "handler": "vk-miniapp-login-v2",
        "endpoint": "/api/v1/auth/vk-miniapp-login",
    }


api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(partners.router)
api_router.include_router(partner.router)
api_router.include_router(privileges.router)
api_router.include_router(clients.router)
api_router.include_router(bot_vk.router)
api_router.include_router(internal.router)
