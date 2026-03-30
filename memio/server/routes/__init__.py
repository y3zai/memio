"""Router aggregation — combines all store routers into one."""

from fastapi import APIRouter

from memio.server.routes.documents import router as documents_router
from memio.server.routes.facts import router as facts_router
from memio.server.routes.graph import router as graph_router
from memio.server.routes.history import router as history_router

router = APIRouter(prefix="/v1")
router.include_router(facts_router)
router.include_router(history_router)
router.include_router(documents_router)
router.include_router(graph_router)
