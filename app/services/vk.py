"""
Интеграция с VK API.

Поток подключения сообщества (то, что просил пользователь — "выбрать своё сообщество"):
  1. Пользователь жмёт "Подключить ВК" -> редирект на oauth.vk.com с scope=groups,offline.
  2. VK возвращает code -> меняем на access_token пользователя.
  3. Через groups.get(filter=admin) получаем список сообществ, где пользователь — админ.
  4. Пользователь выбирает нужные группы в нашем UI.
  5. Запрашиваем ТОКЕНЫ СООБЩЕСТВ (scope=manage,wall,photos) — отдельный OAuth-редирект
     с group_ids=<выбранные>. VK вернёт access_token для каждой группы.
  6. Этими group-токенами публикуем посты от имени сообщества.
"""
import httpx
from urllib.parse import urlencode
from ..config import settings

VK_OAUTH = "https://oauth.vk.com/authorize"
VK_TOKEN = "https://oauth.vk.com/access_token"
VK_API = "https://api.vk.com/method"


# ---------- Шаг 1: ссылка на вход пользователя ----------
def user_auth_url(state: str) -> str:
    """Ссылка, по которой пользователь логинится и даёт доступ к списку своих групп."""
    params = {
        "client_id": settings.VK_CLIENT_ID,
        "redirect_uri": settings.VK_REDIRECT_URI,
        "scope": "groups,offline",   # доступ к списку сообществ
        "response_type": "code",
        "v": settings.VK_API_VERSION,
        "state": state,
    }
    return f"{VK_OAUTH}?{urlencode(params)}"


# ---------- Шаг 5: ссылка на выдачу токенов выбранных сообществ ----------
def community_token_url(group_ids: list[int], state: str) -> str:
    """
    Ссылка для получения ТОКЕНОВ СООБЩЕСТВ.
    group_ids — какие группы пользователь выбрал в нашем UI.
    scope manage,wall,photos = управление, публикация на стене, загрузка картинок.
    """
    params = {
        "client_id": settings.VK_CLIENT_ID,
        "redirect_uri": settings.VK_REDIRECT_URI,
        "scope": "manage,wall,photos",
        "group_ids": ",".join(map(str, group_ids)),
        "response_type": "code",
        "v": settings.VK_API_VERSION,
        "state": state,
    }
    return f"{VK_OAUTH}?{urlencode(params)}"


# ---------- Обмен code -> токены ----------
async def exchange_code(code: str) -> dict:
    """
    Меняет code на токены.
    При обычном входе вернёт {access_token, user_id, ...}.
    При выдаче групп вернёт ещё access_token_<group_id> для каждой группы.
    """
    params = {
        "client_id": settings.VK_CLIENT_ID,
        "client_secret": settings.VK_CLIENT_SECRET,
        "redirect_uri": settings.VK_REDIRECT_URI,
        "code": code,
    }
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(VK_TOKEN, params=params)
        r.raise_for_status()
        return r.json()


def parse_group_tokens(token_response: dict) -> dict[int, str]:
    """Достаёт токены сообществ из ответа VK: ключи вида access_token_12345."""
    result = {}
    for key, value in token_response.items():
        if key.startswith("access_token_"):
            gid = int(key.replace("access_token_", ""))
            result[gid] = value
    return result


# ---------- Список сообществ пользователя ----------
async def get_admin_groups(user_token: str) -> list[dict]:
    """Группы, где пользователь — администратор (для экрана выбора)."""
    params = {
        "filter": "admin",
        "extended": 1,
        "fields": "photo_100,members_count,screen_name",
        "access_token": user_token,
        "v": settings.VK_API_VERSION,
    }
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{VK_API}/groups.get", params=params)
        data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"].get("error_msg", "VK error"))
    return data["response"]["items"]


# ---------- Публикация поста ----------
async def publish_post(group_id: int, group_token: str, message: str,
                       attachments: str | None = None) -> int:
    """
    Публикует пост на стене сообщества от его имени.
    Возвращает vk_post_id. from_group=1 — пост от имени группы, а не пользователя.
    """
    params = {
        "owner_id": -abs(group_id),     # для сообществ id отрицательный
        "from_group": 1,
        "message": message,
        "access_token": group_token,
        "v": settings.VK_API_VERSION,
    }
    if attachments:
        params["attachments"] = attachments
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(f"{VK_API}/wall.post", params=params)
        data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"].get("error_msg", "VK publish error"))
    return data["response"]["post_id"]
