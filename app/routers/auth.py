from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, crud
from app.auth import verify_password
from app.jwt_utils import create_access_token

router = APIRouter(tags=["Auth"])


@router.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_phone(db, user.phone)
    if db_user:
        raise HTTPException(status_code=400, detail="Телефон уже зарегистрирован")
    return crud.create_user(db, user)

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    phone = form_data.username
    password = form_data.password

    user = db.query(models.User).filter(models.User.phone == phone).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid phone or password")

    token = create_access_token(
        {"sub": str(user.id), "is_admin": user.is_admin}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }
