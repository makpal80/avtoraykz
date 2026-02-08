from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from typing import List

class UserCreate(BaseModel):
    phone: str
    name: str
    car_brand: str
    password: str

class UserLogin(BaseModel):
    phone: str
    password: str

class UserOut(BaseModel):
    id: int
    phone: str
    name: str
    car_brand: str
    discount: int

    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    name: str
    price: float
    discount_percent: int = 0

class ProductCreate(ProductBase):
    pass

class ProductOut(ProductBase):
    id: int
    active: bool

    class Config:
        from_attributes = True

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: list[OrderItemCreate]
    payment_method: str

class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    original_price: float
    product_discount_percent: int
    price: float  # after product discount'
    product: ProductOut

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: int
    user_id: int
    user_name: str | None = None 
    user_car: str | None = None 
    total_amount: float
    discount_percent: int
    final_amount: float
    payment_method: str
    status: str
    created_at: datetime
    user_order_number: int
    items: list[OrderItemOut] = [] 

    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    discount_percent: Optional[int] = None
    active: Optional[bool] = None

class MakeAdminRequest(BaseModel):
    user_id: int

class MeOut(BaseModel):
    id: int
    phone: str
    name: str
    car_brand: str
    orders_count: int
    discount: int
    is_admin: bool

    class Config:
        from_attributes = True

class OrdersPageOut(BaseModel):
    items: list[OrderAdminOut]
    total: int
    page: int
    limit: int

class OrderAdminOut(OrderOut):
    user_name: str

OrderAdminOut.model_rebuild()
OrdersPageOut.model_rebuild()
