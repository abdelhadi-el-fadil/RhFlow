from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.ai_offer_service import build_validated_prompt, generate_sync
from app.core.codes import ErrorCode
from app.core.dependencies import get_current_user
from app.core.exceptions import AppException
from app.core.schemas import ApiResponse
from app.database import get_db
from app.domains.recruitment.service import get_project as get_recruitment_project
from app.domains.users.model import User

router = APIRouter(prefix="/ai", tags=["AI"])


class GeneratedOfferResponse(BaseModel):
    offer: str


@router.get(
    "/generate-offer/{projet_id}",
    response_model=ApiResponse[GeneratedOfferResponse],
)
def generate_offer(
    projet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[GeneratedOfferResponse]:
    project = get_recruitment_project(db, projet_id, current_user)
    if project.offre:
        return ApiResponse(data=GeneratedOfferResponse(offer=project.offre))

    prompt = build_validated_prompt(projet_id, db=db, current_user=current_user)

    try:
        offer = generate_sync(prompt)
    except Exception as exc:
        raise AppException(
            status_code=502,
            detail=f"LLM provider error: {exc}",
            code=ErrorCode.INTERNAL_ERROR,
        ) from exc

    project.offre = offer
    project.updated_by_id = current_user.id
    db.add(project)
    db.flush()

    return ApiResponse(data=GeneratedOfferResponse(offer=offer))
