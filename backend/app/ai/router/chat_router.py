from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.ai.service.chat_service import ChatService
from app.core.codes import ErrorCode
from app.core.exceptions import AppException
from app.core.schemas import ApiResponse

router = APIRouter(prefix="/ai", tags=["AI"])
chat_service = ChatService()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ApiResponse[ChatResponse])
async def chat(payload: ChatRequest) -> ApiResponse[ChatResponse]:
    try:
        reply = await chat_service.chat(payload.message)
    except Exception as exc:
        raise AppException(
            status_code=502,
            detail=f"LLM provider error: {exc}",
            code=ErrorCode.INTERNAL_ERROR,
        ) from exc

    return ApiResponse(data=ChatResponse(response=reply))
