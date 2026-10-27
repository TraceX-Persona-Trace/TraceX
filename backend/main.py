from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from .routes.health import router as health_router
from .routes.investigations import router as investigations_router
from .routes.osint import router as osint_router
from .routes.evidence import router as evidence_router
from .routes.seed import router as seed_router
from .routes.reconstruction import router as reconstruction_router
from .routes.matching import router as matching_router
from .routes.intelligence import router as intelligence_router

app = FastAPI(title="TraceX API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(investigations_router)
app.include_router(evidence_router)
app.include_router(seed_router)
app.include_router(reconstruction_router)
app.include_router(matching_router)
app.include_router(intelligence_router)
app.include_router(osint_router)


@app.on_event("startup")
def on_startup():
    init_db()
