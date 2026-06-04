"""
ПостПилот — точка входа FastAPI.
Запуск: uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .db import init_db
from .routers import auth, posts


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="ПостПилот", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(posts.router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}
