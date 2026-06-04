"""
Роутер авторизации и подключения сообществ.

Маршруты:
  GET  /auth/vk/login          -> редирект на VK (вход + доступ к группам)
  GET  /auth/vk/callback       -> единый колбэк VK (обрабатывает оба этапа по state)
  POST /auth/vk/select         -> пользователь выбрал группы, редирект за их токенами
"""
import secrets
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import User, Community
from ..services import vk

router = APIRouter(prefix="/auth/vk", tags=["auth"])

# временное хранилище state (в проде — Redis/сессии)
_pending: dict[str, dict] = {}
# кэш списка групп между callback и UI выбора (в проде — Redis с TTL)
_group_cache: dict[str, list] = {}


@router.get("/groups")
async def groups_for_select(select: str):
    """Фронт забирает список сообществ для экрана выбора по select-state."""
    groups = _group_cache.get(select)
    if groups is None:
        return JSONResponse({"error": "Сессия выбора истекла"}, status_code=404)
    return {"select_state": select, "groups": groups}


@router.get("/login")
async def login():
    """Шаг 1: отправляем пользователя в VK за доступом к списку сообществ."""
    state = secrets.token_urlsafe(16)
    _pending[state] = {"stage": "user"}
    return RedirectResponse(vk.user_auth_url(state))


@router.get("/callback")
async def callback(request: Request, db: AsyncSession = Depends(get_db)):
    """Единый колбэк. Различаем этап по сохранённому state."""
    code = request.query_params.get("code")
    state = request.query_params.get("state", "")
    ctx = _pending.get(state)
    if not code or not ctx:
        return JSONResponse({"error": "Некорректный запрос авторизации"}, status_code=400)

    token_resp = await vk.exchange_code(code)

    # --- Этап А: вход пользователя, показываем список его групп ---
    if ctx["stage"] == "user":
        user_token = token_resp["access_token"]
        vk_user_id = token_resp["user_id"]

        # сохраняем/обновляем пользователя
        res = await db.execute(select(User).where(User.vk_user_id == vk_user_id))
        user = res.scalar_one_or_none()
        if not user:
            user = User(vk_user_id=vk_user_id)
            db.add(user)
            await db.commit()
            await db.refresh(user)

        groups = await vk.get_admin_groups(user_token)
        # новый state для следующего этапа
        sel_state = secrets.token_urlsafe(16)
        _pending[sel_state] = {"stage": "select", "user_id": user.id}
        _pending.pop(state, None)

        # кэшируем список групп для фронта и редиректим на UI выбора
        _group_cache[sel_state] = [
            {"id": g["id"], "name": g["name"],
             "photo": g.get("photo_100", ""),
             "members": g.get("members_count", 0)}
            for g in groups
        ]
        return RedirectResponse(f"/?select={sel_state}")

    # --- Этап Б: получили токены выбранных сообществ, сохраняем ---
    if ctx["stage"] == "tokens":
        user_id = ctx["user_id"]
        group_tokens = vk.parse_group_tokens(token_resp)
        groups_meta = ctx.get("groups_meta", {})

        for gid, gtoken in group_tokens.items():
            meta = groups_meta.get(gid, {})
            res = await db.execute(
                select(Community).where(Community.vk_group_id == gid,
                                        Community.owner_id == user_id))
            comm = res.scalar_one_or_none()
            if comm:
                comm.group_token = gtoken
            else:
                db.add(Community(
                    owner_id=user_id, vk_group_id=gid, group_token=gtoken,
                    name=meta.get("name", ""), photo_url=meta.get("photo", ""),
                    members_count=meta.get("members", 0),
                ))
        await db.commit()
        _pending.pop(state, None)
        return RedirectResponse("/?connected=1")

    return JSONResponse({"error": "Неизвестный этап"}, status_code=400)


@router.post("/select")
async def select_communities(payload: dict):
    """
    Шаг 4->5: пользователь выбрал группы в UI.
    payload = {"select_state": "...", "groups": [{"id":..,"name":..,"photo":..,"members":..}]}
    Возвращаем ссылку, по которой VK выдаст токены этих сообществ.
    """
    sel_state = payload.get("select_state", "")
    ctx = _pending.get(sel_state)
    if not ctx or ctx["stage"] != "select":
        return JSONResponse({"error": "Сессия выбора истекла"}, status_code=400)

    chosen = payload.get("groups", [])
    group_ids = [g["id"] for g in chosen]
    if not group_ids:
        return JSONResponse({"error": "Не выбрано ни одного сообщества"}, status_code=400)

    token_state = secrets.token_urlsafe(16)
    _pending[token_state] = {
        "stage": "tokens",
        "user_id": ctx["user_id"],
        "groups_meta": {g["id"]: g for g in chosen},
    }
    _pending.pop(sel_state, None)
    return {"redirect": vk.community_token_url(group_ids, token_state)}
