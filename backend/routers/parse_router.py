from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm", tags=["llm-parsing"])

@router.get("/status")
async def get_llm_status():
    """Get LLM service status"""
    return {"status": "active", "service": "llm-parsing"}