"""
Роутер работы с постами.

Маршруты:
  GET  /api/communities                  -> список подключённых сообществ
  POST /api/generate                     -> сгенерировать текст поста (LLM)
  POST /api/publish                      -> опубликовать пост в выбранное сообщество
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import Community, Post
from ..services import generator, vk

router = APIRouter(prefix="/api", tags=["posts"])


class GenerateIn(BaseModel):
    community_id: int
    topic: str
    tone: str = "дружеский"
    format: str = "анонс"


class PublishIn(BaseModel):
    community_id: int
    text: str
    schedule_at: datetime | None = None  # если задано — в очередь, иначе сразу


@router.get("/communities")
async def list_communities(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Community))
    items = res.scalars().all()
    return [
        {"id": c.id, "vk_group_id": c.vk_group_id, "name": c.name,
         "photo": c.photo_url, "members": c.members_count}
        for c in items
    ]


@router.post("/generate")
async def generate(body: GenerateIn, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Community).where(Community.id == body.community_id))
    comm = res.scalar_one_or_none()
    community_name = comm.name if comm else ""

    text = await generator.generate_post(body.topic, body.tone, body.format, community_name)

    # сохраняем черновик
    post = Post(community_id=body.community_id, text=text, topic=body.topic,
                tone=body.tone, format=body.format, status="draft")
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return {"post_id": post.id, "text": text}


@router.post("/publish")
async def publish(body: PublishIn, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Community).where(Community.id == body.community_id))
    comm = res.scalar_one_or_none()
    if not comm:
        return JSONResponse({"error": "Сообщество не найдено"}, status_code=404)

    # отложенная публикация -> в очередь (обрабатывается планировщиком)
    if body.schedule_at and body.schedule_at > datetime.now(timezone.utc):
        post = Post(community_id=comm.id, text=body.text, status="queued",
                    publish_at=body.schedule_at)
        db.add(post)
        await db.commit()
        return {"status": "queued", "publish_at": body.schedule_at.isoformat()}

    # немедленная публикация
    try:
        vk_post_id = await vk.publish_post(comm.vk_group_id, comm.group_token, body.text)
    except Exception as e:
        return JSONResponse({"error": f"Ошибка публикации VK: {e}"}, status_code=502)

    post = Post(community_id=comm.id, text=body.text, status="published",
                vk_post_id=vk_post_id)
    db.add(post)
    await db.commit()
    return {"status": "published", "vk_post_id": vk_post_id,
            "url": f"https://vk.com/wall-{comm.vk_group_id}_{vk_post_id}"}
