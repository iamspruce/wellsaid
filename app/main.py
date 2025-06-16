from fastapi import FastAPI
from app.routers import analyze, paraphrase, translate, summarize

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Welcome to Grammafree API"}

app.include_router(analyze.router)
app.include_router(paraphrase.router)
app.include_router(translate.router)
app.include_router(summarize.router)
