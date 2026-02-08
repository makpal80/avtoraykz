from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas

router = APIRouter(tags=["Public"])

@router.get("/products", response_model=list[schemas.ProductOut])
def list_public_products(db: Session = Depends(get_db)):
    return crud.get_active_products(db)
