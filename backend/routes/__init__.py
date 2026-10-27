from .health import router as health_router
from .investigations import router as investigations_router
from .evidence import router as evidence_router
from .seed import router as seed_router
from .reconstruction import router as reconstruction_router
from .matching import router as matching_router
from .intelligence import router as intelligence_router

__all__ = [
    "health_router",
    "investigations_router",
    "evidence_router",
    "seed_router",
    "reconstruction_router",
    "matching_router",
    "intelligence_router",
]
