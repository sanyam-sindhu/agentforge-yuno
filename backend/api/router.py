from fastapi import APIRouter
from .agents import router as agents_router
from .workflows import router as workflows_router
from .executions import router as executions_router
from .messages import router as messages_router

api_router = APIRouter(prefix="/api")
api_router.include_router(agents_router)
api_router.include_router(workflows_router)
api_router.include_router(executions_router)
api_router.include_router(messages_router)
