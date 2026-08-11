import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend.auth.routes import router as auth_router
from backend.routes.analyze import router as analyze_router
from backend.routes.history import router as history_router
from backend.routes.jd_library import router as jd_library_router
from backend.routes.batch_analyze import router as batch_analyze_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        try:
            import huggingface_hub
            huggingface_hub.login(token=hf_token, add_to_git_credential=False)
            print("[startup] HuggingFace Hub authenticated successfully.")
        except Exception as exc:
            print(f"[startup] HuggingFace Hub login failed ({exc}) — continuing without auth.")
    else:
        print("[startup] No HF_TOKEN set — using unauthenticated HuggingFace Hub access.")

    try:
        from utils.esco_loader import ESCOLoader
        from matching.semantic_matcher import get_model

        esco = ESCOLoader("data/esco/")
        if esco.is_loaded:
            model = get_model()
            esco.build_index(model, cache_dir="data/esco/cache/")
            app.state.esco = esco
            print("[startup] ESCO index ready — "
                  f"{len(esco._occ_uris)} occupations, "
                  f"{len(esco._skills_index)} skills indexed.")
        else:
            app.state.esco = None
            print("[startup] ESCO data not found — running without role taxonomy.")
    except Exception as exc:
        app.state.esco = None
        print(f"[startup] ESCO initialisation failed ({exc}) — continuing without it.")

    yield


app = FastAPI(
    title="Hybrid AI ATS Engine",
    version="2.0",
    description="Backend API for Resume Analysis with JWT Auth and SQLite/PostgreSQL",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(analyze_router)
app.include_router(history_router)
app.include_router(jd_library_router)
app.include_router(batch_analyze_router)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Hybrid AI ATS Engine running."}
