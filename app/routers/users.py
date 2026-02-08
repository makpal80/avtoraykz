from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app import schemas, models

router = APIRouter(tags=["Users"])

@router.get("/me", response_model=schemas.MeOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user
