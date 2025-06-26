from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from app.routers import (
    grammar,
    tone,
    voice,
    inclusive_language,
    readability,
    paraphrase,
    translate,
    rewrite,
)

def create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(GZipMiddleware, minimum_size=500)
    
    app.include_router(grammar.router)
    app.include_router(tone.router)
    app.include_router(voice.router)
    app.include_router(inclusive_language.router)
    app.include_router(readability.router)
    app.include_router(paraphrase.router)
    app.include_router(translate.router)
    app.include_router(rewrite.router)

    @app.get("/")
    def root():
        return {"message": "Welcome to Grammafree API"}

    return app
