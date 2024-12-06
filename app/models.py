from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text   
from sqlalchemy.schema import CheckConstraint
from .database import Base
from datetime import datetime

import enum

class UserRole(enum.Enum):
    CUSTOMER = "CUSTOMER"
    SELLER = "SELLER"
    ADMIN = "ADMIN"
    
    def __str__(self):
        return self.value
    
class OrderStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String(10), unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    cart = relationship("Cart", back_populates="user")
    products = relationship("Product", back_populates="owner")
    orders = relationship("Order", back_populates="user")
    shipping_addresses = relationship("ShippingAddress", back_populates="user")


    __table_args__ = (
        CheckConstraint('length(phone_number) = 10', name='check_phone_number_length'),
    )
    
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    discount_price = Column(Float, nullable=True)
    sale_start_date = Column(DateTime, nullable=True)
    sale_end_date = Column(DateTime, nullable=True)
    stock = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    category = Column(String, nullable=False)
    brand = Column(String, nullable=False) 
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    owner = relationship("User", back_populates="products")
    # reviews = relationship("Review", back_populates="product")

    __table_args__ = (
        CheckConstraint('price > 0', name='check_price_positive'),
        CheckConstraint('stock >= 0', name='check_stock_non_negative'),
    )
   
class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    
    items = relationship("CartItem", back_populates="cart")
    user = relationship("User", back_populates="cart")

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1)
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
    )

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")

class ShippingAddress(Base):
    __tablename__ = "shipping_addresses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    street = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    country = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="shipping_addresses")
    


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    shipping_address_id = Column(Integer, ForeignKey("shipping_addresses.id", ondelete="CASCADE"), nullable=False)
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    shipping_address = relationship("ShippingAddress")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    
class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    blacklisted_at = Column(DateTime, default=datetime.utcnow)
    expiry_time = Column(DateTime)




## ToDo : need to add reviw schema

# class Review(Base):
#     __tablename__ = "reviews"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
#     product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
#     rating = Column(Integer, nullable=False)
#     comment = Column(Text, nullable=True)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

#     user = relationship("User", back_populates="reviews")
#     product = relationship("Product", back_populates="reviews")

#     __table_args__ = (
#         CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
#     )

# # Update User model to include new relationships
# class User(Base):
#     __tablename__ = "users"
#     # ... existing fields ...

#     orders = relationship("Order", back_populates="user")
#     reviews = relationship("Review", back_populates="user")
