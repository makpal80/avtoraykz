from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import os
from app.database import engine, get_db
from app import models, schemas, crud
from app.auth import verify_password
from app.routers import admin, orders, auth, public, users
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Autoray")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://avtoray.vercel.app", "https://avtoray.kz", "https://www.avtoray.kz",],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(public.router)
app.include_router(admin.router)
app.include_router(orders.router)
app.include_router(users.router)

@app.get("/")
def root():
    return {"status": "backend работает"}

@app.post("/seed-admin")
def seed_admin(
    user_id: int,
    x_seed_key: str = Header(None),
    db: Session = Depends(get_db)
):
    if x_seed_key != os.getenv("ADMIN_SEED_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        user = crud.make_user_admin(db, user_id)
        return {"ok": True, "user_id": user.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
