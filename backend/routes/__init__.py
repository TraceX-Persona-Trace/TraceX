from routes.health import router as health_router
from routes.investigations import router as investigations_router
from routes.evidence import router as evidence_router
from routes.seed import router as seed_router
from routes.reconstruction import router as reconstruction_router
from routes.matching import router as matching_router
from routes.intelligence import router as intelligence_router

__all__ = [
    "health_router",
    "investigations_router",
    "evidence_router",
    "seed_router",
    "reconstruction_router",
    "matching_router",
    "intelligence_router",
]
