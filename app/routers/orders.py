from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_current_user
from app.database import get_db
from app import schemas, crud, models

router = APIRouter(tags=["Orders"])

@router.post("/orders", response_model=schemas.OrderOut)
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.create_order(db, current_user, order)

@router.get("/orders", response_model=list[schemas.OrderOut])
def my_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.get_user_orders(db, current_user.id)

@router.get("/products", response_model=list[schemas.ProductOut])
def list_products(db: Session = Depends(get_db)):
    return crud.get_active_products(db)