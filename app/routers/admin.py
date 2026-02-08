from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO
from datetime import datetime
from app.database import get_db
from app import crud, schemas, models
from app.deps import get_current_admin


router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(get_current_admin)])

PAYMENT_LABELS = {
    "cash": "Наличные",
    "bank": "Банк / перевод",
}

STATUS_LABELS = {
    "pending": "Ожидает подтверждения",
    "approved": "Подтверждён",
    "rejected": "Отклонён",
}

@router.post("/products", response_model=schemas.ProductOut)
def add_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db)
):
    return crud.create_product(db, product)


@router.get("/products", response_model=list[schemas.ProductOut])
def list_products(db: Session = Depends(get_db)):
    return crud.admin_get_products(db)   

@router.patch("/orders/{order_id}/approve", response_model=schemas.OrderOut)
def approve_order(order_id: int, db: Session = Depends(get_db)):
    try:
        return crud.approve_order(db, order_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) 

@router.patch("/orders/{order_id}/reject", response_model=schemas.OrderOut)
def reject_order(order_id: int, db: Session = Depends(get_db)):
    try:
        return crud.reject_order(db, order_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/reports/excel")
def export_orders_excel(
    date_from: str,
    date_to: str,
    db: Session = Depends(get_db)
):

    try:
        start = datetime.fromisoformat(date_from)
        end = datetime.fromisoformat(date_to)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    orders = crud.get_orders_for_report(db, start, end)

    # формируем данные
    rows = []
    for o in orders:
        rows.append({
            "Дата": o.created_at.strftime("%d.%m.%Y"),
            "Клиент": o.user.name,
            "Телефон": o.user.phone,
            "Марка авто": o.user.car_brand,
            "Сумма": o.total_amount,
            "Скидка %": o.discount_percent,
            "Итого": o.final_amount,
            "Метод оплаты": PAYMENT_LABELS.get(o.payment_method, o.payment_method),
            "Статус": STATUS_LABELS.get(o.status, o.status)
        })

    df = pd.DataFrame(rows)

    # пишем в Excel в памяти
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Orders")

    output.seek(0)

    filename = f"orders_{date_from}_to_{date_to}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
@router.get("/reports/client/{user_id}/excel")
def export_client_report_excel(
    user_id: int,
    date_from: str,   # YYYY-MM-DD
    date_to: str,     # YYYY-MM-DD
    db: Session = Depends(get_db)
):
    # даты: ISO формат, период включительно
    try:
        start = datetime.fromisoformat(date_from)  # 2026-01-01
        end = datetime.fromisoformat(date_to)      # 2026-01-31
        end = end.replace(hour=23, minute=59, second=59)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    orders = crud.get_client_orders_with_items(db, user_id, start, end)

    # 1) Таблица "Покупки" (строка = товар в заказе)
    rows = []
    for o in orders:
        for it in o.items:
            product_name = it.product.name if it.product else f"product_id={it.product_id}"
            line_total = float(it.price) * int(it.quantity)

            rows.append({
                "Дата": o.created_at.strftime("%d.%m.%Y"),
                "Заказ ID": o.id,
                "Статус": STATUS_LABELS.get(o.status, o.status),
                "Метод оплаты": PAYMENT_LABELS.get(o.payment_method, o.payment_method),

                "Товар": product_name,
                "Кол-во": it.quantity,
                "Цена за шт": float(it.price),
                "Сумма по позиции": line_total,

                "Скидка заказа %": o.discount_percent,
                "Итого по заказу": float(o.final_amount),
            })

    df_items = pd.DataFrame(rows)

    # 2) Таблица "Сводка по заказам" (строка = заказ)
    summary_rows = []
    for o in orders:
        summary_rows.append({
            "Дата": o.created_at.strftime("%d.%m.%Y"),
            "Заказ ID": o.id,
            "Статус": STATUS_LABELS.get(o.status, o.status),
            "Метод оплаты": PAYMENT_LABELS.get(o.payment_method, o.payment_method),
            "Сумма": float(o.total_amount),
            "Скидка %": o.discount_percent,
            "Итого": float(o.final_amount),
            "Кол-во позиций": len(o.items)
        })

    df_orders = pd.DataFrame(summary_rows)

    # Excel в памяти
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_client = pd.DataFrame([{
            "Клиент": user.name,
            "Телефон": user.phone,
            "Марка авто": user.car_brand,
            "Заказов подтверждено": user.orders_count,
            "Текущая скидка %": user.discount
        }])
        df_client.to_excel(writer, index=False, sheet_name="Клиент")
        df_orders.to_excel(writer, index=False, sheet_name="Заказы")
        df_items.to_excel(writer, index=False, sheet_name="Покупки")

    output.seek(0)

    filename = f"client_{user_id}_{date_from}_to_{date_to}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
@router.patch("/products/{product_id}", response_model=schemas.ProductOut)
def update_product(
    product_id: int,
    payload: schemas.ProductUpdate,
    db: Session = Depends(get_db)
):
    return crud.update_product(db, product_id, payload)

@router.patch("/users/make-admin", response_model=schemas.UserOut)
def make_admin(
    payload: schemas.MakeAdminRequest,
    db: Session = Depends(get_db)
):
    try:
        return crud.make_user_admin(db, payload.user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/orders", response_model=schemas.OrdersPageOut)
def list_orders(
    page: int = 1,
    limit: int = 10,
    q: str | None = None,
    status: str | None = "all",
    db: Session = Depends(get_db),
):
    return crud.admin_get_orders(db, page=page, limit=limit, q=q, status=status)

@router.get("/orders/count")
def orders_count(db: Session = Depends(get_db)):
    return {"total": crud.admin_orders_count(db)}

@router.get("/orders/{order_id}")
def get_order_details(order_id: int, db: Session = Depends(get_db)):
    o = (
        db.query(models.Order)
        .options(joinedload(models.Order.user), joinedload(models.Order.items).joinedload(models.OrderItem.product))
        .filter(models.Order.id == order_id)
        .first()
    )
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "id": o.id,
        "user_id": o.user_id,
        "user_name": o.user.name if o.user else "—",
        "status": o.status,
        "payment_method": o.payment_method,
        "discount_percent": o.discount_percent,
        "total_amount": float(o.total_amount),
        "final_amount": float(o.final_amount),
        "created_at": o.created_at.isoformat(),
        "items": [
            {
                "id": it.id,
                "product_id": it.product_id,
                "product_name": it.product.name if it.product else "—",
                "quantity": it.quantity,
                "original_price": float(getattr(it, "original_price", it.price)),  # на всякий
                "price": float(it.price),
                "product_discount_percent": int(getattr(it, "product_discount_percent", 0)),
                "line_total": float(it.price) * int(it.quantity),
            }
            for it in o.items
        ],
    }