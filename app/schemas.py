from pydantic import BaseModel, EmailStr, HttpUrl, field_validator, constr
from typing import List, Optional
from enum import Enum
from typing import List
from datetime import datetime


from enum import Enum

class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    SELLER = "SELLER"
    ADMIN = "ADMIN"
    
    def __str__(self):
        return self.value
    
class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class UserBase(BaseModel):
    user_name: str
    email: EmailStr
    role: Optional[UserRole] = UserRole.CUSTOMER
    phone_number: constr(min_length=10, max_length=10)
    
    class Config:
        from_attributes = True
        use_enum_values = True

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True
        
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: str
    role: Optional[str] = None

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    discount_price: Optional[float] = None
    sale_start_date: Optional[datetime] = None
    sale_end_date: Optional[datetime] = None
    stock: int
    is_active: Optional[bool] = True
    category: str
    brand: str 
    image_url: Optional[HttpUrl] = None
    
    @field_validator("image_url")
    def convert_url_to_str(cls, value):
        return str(value) if value else None

    @field_validator("price", "discount_price")
    def check_price_positive(cls, value):
        if value is not None and value <= 0:
            raise ValueError("Price must be positive")
        return value

    @field_validator("stock")
    def check_stock_non_negative(cls, value):
        if value < 0:
            raise ValueError("Stock cannot be negative")
        return value

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    discount_price: Optional[float] = None
    sale_start_date: Optional[datetime] = None
    sale_end_date: Optional[datetime] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    
    @field_validator("image_url")
    def convert_url_to_str(cls, value):
        return str(value) if value else None

    @field_validator("price", "discount_price")
    def check_price_positive(cls, value):
        if value is not None and value <= 0:
            raise ValueError("Price must be positive")
        return value

    @field_validator("stock")
    def check_stock_non_negative(cls, value):
        if value is not None and value < 0:
            raise ValueError("Stock cannot be negative")
        return value

class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: int

    class Config:
        from_attributes = True

class CartItemBase(BaseModel):
    product_id: int
    quantity: int

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int

class CartItem(CartItemBase):
    id: int
    
    class Config:
        from_attributes = True

class CartTotal(BaseModel):
    total: float
    items_count: int

class CartBase(BaseModel):
    items: List[CartItem] = []

class CartCreate(CartBase):
    pass

class Cart(CartBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class ShippingAddressBase(BaseModel):
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str

class ShippingAddressCreate(ShippingAddressBase):
    pass

class ShippingAddress(ShippingAddressBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderItem(OrderItemBase):
    id: int

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    shipping_address_id: int

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    items: List[OrderItem]

    class Config:
        from_attributes = True
        
class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class ShippingAddressBase(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    
class ShippingAddressCreate(ShippingAddressBase):
    pass

class ShippingAddress(ShippingAddressBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
