from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from limitboard_server.api.routes import router
from limitboard_server.config import settings
from limitboard_server.scheduler import FetchScheduler

scheduler = FetchScheduler()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.scheduler_enabled:
        await asyncio.to_thread(scheduler.catch_up_missing_trading_days)
        scheduler.start()
    try:
        yield
    finally:
        if settings.scheduler_enabled:
            scheduler.stop()


app = FastAPI(title="AlphaScope Server", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")
