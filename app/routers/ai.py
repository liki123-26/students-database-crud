from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import httpx

from app.database import get_db
from app.config import settings
from app.schemas import AIQueryRequest, AIQueryResponse
from app.services.ai_service import query_ollama_ai

router = APIRouter(
    prefix="/ai",
    tags=["Optional AI Extension (Ollama)"]
)


@router.post(
    "/ask",
    response_model=AIQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask questions about student records in natural language",
    description=(
        "Accepts questions such as 'How many students are there?' or 'List students born after 2005.' "
        "Securely retrieves relevant SQLite records and grounds the response using local Ollama model "
        "(or built-in grounded fallback engine if Ollama is not active)."
    )
)
async def ask_student_database(
    request: AIQueryRequest,
    db: Session = Depends(get_db)
):
    result = await query_ollama_ai(
        db=db,
        question=request.question,
        model_override=request.model
    )
    return AIQueryResponse(**result)


@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="Check Ollama local connection status",
    description="Tests connection to the configured Ollama server and returns health details."
)
async def check_ollama_status() -> Dict[str, Any]:
    ollama_url = settings.ollama_base_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{ollama_url}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {
                    "ollama_available": True,
                    "ollama_url": ollama_url,
                    "configured_model": settings.ollama_model,
                    "installed_models": models,
                    "message": "Ollama is running and ready for AI queries."
                }
    except Exception as ex:
        pass

    return {
        "ollama_available": False,
        "ollama_url": ollama_url,
        "configured_model": settings.ollama_model,
        "installed_models": [],
        "message": (
            f"Ollama server is currently not reachable at {ollama_url}. "
            "Grounded fallback engine will be used automatically. "
            f"To run local AI, install Ollama and run: 'ollama run {settings.ollama_model}'."
        )
    }
