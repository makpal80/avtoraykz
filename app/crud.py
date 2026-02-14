from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from . import models, schemas
from .auth import hash_password
from app.services.discount import calculate_discount

from datetime import datetime

def create_user(db: Session, user):
    db_user = models.User(
        phone=user.phone,
        name=user.name,
        car_brand=user.car_brand,
        hashed_password=hash_password(user.password),
        discount=calculate_discount(0),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_phone(db: Session, phone: str):
    return db.query(models.User).filter(models.User.phone == phone).first()

def create_product(db: Session, product: schemas.ProductCreate):
    new_product = models.Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

def get_active_products(db: Session):
    return db.query(models.Product).filter(models.Product.active == True).all()

def admin_get_products(db: Session):
    return db.query(models.Product).all()

def create_order(db: Session, user: models.User, order: schemas.OrderCreate):
    items_db = []
    total_amount = 0.0

    for it in order.items:
        product = db.query(models.Product).filter(models.Product.id == it.product_id).first()
        if not product or not product.active:
            raise ValueError("Product not found or inactive")

        prod_disc = int(product.discount_percent or 0)
        original_price = float(product.price)

        unit_price = original_price * (1 - prod_disc / 100)
        line_total = unit_price * it.quantity
        total_amount += line_total

        items_db.append(models.OrderItem(
            product_id=product.id,
            quantity=it.quantity,
            original_price=original_price,
            product_discount_percent=prod_disc,
            price=unit_price,
        ))

    user_discount_percent = int(user.discount or 0)
    final_amount = total_amount * (1 - user_discount_percent / 100)

    if order.payment_method == "installment":
        final_amount *= 1.15

    final_amount = round(final_amount)


    last_num = (
        db.query(func.max(models.Order.user_order_number))
        .filter(models.Order.user_id == user.id)
        .scalar()
    )
    next_num = (last_num or 0) + 1

    new_order = models.Order(
        user_id=user.id,
        user_order_number=next_num,  
        total_amount=total_amount,
        discount_percent=user_discount_percent,
        final_amount=final_amount,
        payment_method=order.payment_method,
        status="pending",
        items=items_db,
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order


def approve_order(db: Session, order_id: int):
    order = (
        db.query(models.Order)
        .options(joinedload(models.Order.user), joinedload(models.Order.items))
        .filter(models.Order.id == order_id)
        .first()
    )
    if not order:
        raise ValueError("Order not found")

    if order.status == "approved":
        return order

    order.status = "approved"

    user = order.user  
    if not user:
        raise ValueError("User not found")

    user.orders_count += 1
    user.discount = calculate_discount(user.orders_count)

    db.commit()
    db.refresh(order)
    return order

def reject_order(db: Session, order_id: int):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise ValueError("Order not found")

    if order.status != "pending":
        raise ValueError("Only pending orders can be rejected")

    order.status = "rejected"
    db.commit()
    db.refresh(order)
    return order

def get_user_orders(db: Session, user_id: int):
    return (
        db.query(models.Order)
        .options(joinedload(models.Order.items))
        .filter(models.Order.user_id == user_id)
        .all()
    )


def get_orders_for_report(db: Session, date_from: datetime, date_to: datetime):
    return (
        db.query(models.Order)
        .join(models.User)
        .filter(models.Order.created_at >= date_from)
        .filter(models.Order.created_at <= date_to)
        .all()
    )

def get_client_orders_with_items(db, user_id: int, date_from: datetime, date_to: datetime):
    return (
        db.query(models.Order)
        .options(joinedload(models.Order.items).joinedload(models.OrderItem.product))
        .filter(models.Order.user_id == user_id)
        .filter(models.Order.created_at >= date_from)
        .filter(models.Order.created_at <= date_to)
        .order_by(models.Order.created_at.desc())
        .all()
    )

def update_product(db: Session, product_id: int, payload):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise ValueError("Product not found")

    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(product, k, v)

    db.commit()
    db.refresh(product)
    return product

def make_user_admin(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    user.is_admin = True
    db.commit()
    db.refresh(user)
    return user

def admin_get_orders(db: Session, page: int = 1, limit: int = 10, q: str | None = None,  status: str | None = None):
    if page < 1: page = 1
    if limit < 1: limit = 10
    if limit > 100: limit = 100

    query = (
      db.query(models.Order)
      .options(joinedload(models.Order.user))  # чтобы o.user не грузился отдельными запросами
      .join(models.User)
    )

    if status and status != "all":
        query = query.filter(models.Order.status == status)

    if q:
        q_like = f"%{q.strip()}%"
        query = query.filter(
            (models.User.name.ilike(q_like)) | (models.User.phone.ilike(q_like))
        )

    total = query.count()

    items = (
        query
        .order_by(models.Order.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "items": [
            {
                "id": o.id,
                "user_id": o.user_id,
                "user_name": o.user.name,
                "user_order_number": o.user_order_number,
                "user_car": o.user.car_brand,
                "total_amount": o.total_amount,
                "discount_percent": o.discount_percent,
                "final_amount": o.final_amount,
                "payment_method": o.payment_method,
                "status": o.status,
                "created_at": o.created_at,
            }
            for o in items
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }
    
def admin_orders_count(db: Session):
    return db.query(func.count(models.Order.id)).scalar() or 0
