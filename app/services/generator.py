"""
Генерация текста поста.
Использует Anthropic API; при отсутствии ключа/ошибке — шаблонный фолбэк,
чтобы сервис не падал в проде.
"""
import httpx
from ..config import settings

SYSTEM_PROMPT = (
    "Ты — SMM-редактор для сообществ ВКонтакте. "
    "Пиши готовый пост на русском: цепляющий, живой, без канцелярита. "
    "Длина 350–700 символов. В конце добавь 3–5 релевантных хештегов. "
    "Не используй markdown и заголовки — это пост для соцсети."
)


def _user_prompt(topic: str, tone: str, fmt: str, community: str) -> str:
    return (
        f"Сообщество: {community}\n"
        f"Тема поста: {topic}\n"
        f"Тон: {tone}\n"
        f"Формат: {fmt}\n\n"
        f"Напиши пост."
    )


def _fallback(topic: str, tone: str, fmt: str) -> str:
    openers = {
        "дружеский": "Друзья, есть новости! 🎉",
        "экспертный": "Делимся важной информацией.",
        "продающий": "Успейте — предложение ограничено! 🔥",
        "тёплый": "Дорогие наши, хотим поделиться 💛",
    }
    tail = {
        "анонс": "Подробности — ниже. Ждём вас!",
        "вопрос дня": "А что думаете вы? Пишите в комментариях 👇",
        "польза": "Сохраняйте, чтобы не потерять 📌",
        "акция": "Только до конца недели на специальных условиях.",
    }
    o = openers.get(tone, openers["дружеский"])
    t = tail.get(fmt, tail["анонс"])
    return f"{o}\n\n{topic.strip().capitalize()}\n\n{t}\n\n#сообщество #новости #ВК"


async def generate_post(topic: str, tone: str, fmt: str, community: str = "") -> str:
    """Генерирует текст поста. Возвращает строку, готовую к публикации."""
    if not settings.ANTHROPIC_API_KEY:
        return _fallback(topic, tone, fmt)

    payload = {
        "model": settings.LLM_MODEL,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": _user_prompt(topic, tone, fmt, community)}],
    }
    headers = {
        "x-api-key": settings.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=40) as c:
            r = await c.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        # собираем текст из блоков ответа
        return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip() \
            or _fallback(topic, tone, fmt)
    except Exception:
        return _fallback(topic, tone, fmt)
