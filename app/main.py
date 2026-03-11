from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.agent import router as agent_router
from app.api.routes.briefs import router as briefs_router
from app.api.routes.competition import router as competition_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router
from app.api.routes.quality import router as quality_router
from app.api.routes.reports import router as reports_router
from app.api.routes.risk import router as risk_router
from app.api.routes.universe import router as universe_router
from app.api.routes.web import router as web_router
from app.api.routes.warehouse import router as warehouse_router
from app.config import settings
from app.core.container import build_service_container
from app.db import init_db


BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.container = build_service_container()
    yield



def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list or ['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.mount('/static', StaticFiles(directory=BASE_DIR / 'static'), name='static')
    app.include_router(web_router)
    app.include_router(agent_router)
    app.include_router(briefs_router)
    app.include_router(competition_router)
    app.include_router(risk_router)
    app.include_router(dashboard_router)
    app.include_router(reports_router)
    app.include_router(quality_router)
    app.include_router(universe_router)
    app.include_router(warehouse_router)
    app.include_router(health_router)
    return app


app = create_app()
