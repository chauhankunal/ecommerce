from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from passlib.context import CryptContext

from .. import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_products(db: Session, skip: int = 0, limit: int = 100, include_inactive: bool = False):
    query = db.query(models.Product)
    if not include_inactive:
        query = query.filter(models.Product.is_active == True)
    return query.offset(skip).limit(limit).all()

# data = crud.create_product(db=db, product=product, owner_id=current_user.id)
def create_product(db: Session, product: schemas.ProductCreate, owner_id: int):
    db_product = models.Product(owner_id=owner_id, **product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, db_product: models.Product, product_update: schemas.ProductUpdate) -> models.Product:
    update_data = product_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    try:
        db.commit()
        db.refresh(db_product)
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"An error occurred while updating the product: {str(e)}")
    
    return db_product

def delete_product(db: Session, db_product: models.Product):
    try:
        db.delete(db_product)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"An error occurred while updating the product: {str(e)}")

def search_products(db: Session, category: str = None, brand: str = None, 
                    min_price: float = None, max_price: float = None, 
                    is_active: bool = None, on_sale: bool = None):
    query = db.query(models.Product)

    if category:
        query = query.filter(models.Product.category.ilike(f"%{category}%"))
    if brand:
        query = query.filter(models.Product.brand.ilike(f"%{brand}%"))

    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)
    if is_active is not None:
        query = query.filter(models.Product.is_active == is_active)
    if on_sale is not None:
        now = datetime.utcnow()
        if on_sale:
            query = query.filter(
                models.Product.discount_price.isnot(None),
                models.Product.sale_start_date <= now,
                models.Product.sale_end_date >= now
            )
        else:
            query = query.filter(
                (models.Product.discount_price.is_(None)) |
                (models.Product.sale_start_date > now) |
                (models.Product.sale_end_date < now)
            )

    return query.all()
