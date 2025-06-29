import os
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from app.routers import grammar, tone, voice, inclusive_language, readability, paraphrase, translate, rewrite, analyze
from app.queue import start_workers
from app.core.middleware import setup_middlewares

@asynccontextmanager
async def lifespan(app: FastAPI):
    num_workers = int(os.getenv("WORKER_COUNT", 4))
    start_workers(num_workers)
    yield

def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.add_middleware(GZipMiddleware, minimum_size=500)
    setup_middlewares(app)

    for router, tag in [
        (grammar.router, "Grammar"),
        (tone.router, "Tone"),
        (voice.router, "Voice"),
        (inclusive_language.router, "Inclusive Language"),
        (readability.router, "Readability"),
        (paraphrase.router, "Paraphrasing"),
        (translate.router, "Translation"),
        (rewrite.router, "Rewrite"),
        (analyze.router, "Analyze")
    ]:
        app.include_router(router, tags=[tag])

    @app.get("/")
    def root():
        return {"message": "Welcome to Wellsaid API"}

    return app