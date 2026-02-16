from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from .database import Base
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import UniqueConstraint


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    name = Column(String)
    car_brand = Column(String)
    hashed_password = Column(String)
    orders_count = Column(Integer, default=0)
    discount = Column(Integer, default=3)
    orders = relationship("Order", back_populates="user")
    is_admin = Column(Boolean, default=False)


class ProductType(Base):
    __tablename__ = "product_types"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    image_url = Column(String, nullable=False)

    product = relationship("Product", back_populates="types")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    discount_percent = Column(Integer, default=0)
    types = relationship("ProductType", back_populates="product", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float)
    discount_percent = Column(Integer)
    final_amount = Column(Float)
    payment_method = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    user_order_number = Column(Integer, nullable=False, default=1)
    @property
    def user_name(self):
        return self.user.name if self.user else None

    @property
    def user_car(self):
        return self.user.car_brand if self.user else None

    __table_args__ = (
    UniqueConstraint("user_id", "user_order_number", name="uq_user_order_number"),
    )

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    quantity = Column(Integer, default=1)

    # СНИМОК на момент заказа:
    original_price = Column(Float, nullable=False)              # цена товара без скидки
    product_discount_percent = Column(Integer, default=0)       # скидка товара (%)
    price = Column(Float, nullable=False)                       # цена за 1 шт ПОСЛЕ скидки товара

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    product_type_id = Column(Integer, ForeignKey("product_types.id"), nullable=True)
    type = relationship("ProductType")



