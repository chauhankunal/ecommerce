from fastapi import HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext 
   
from .. import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_cart(db: Session, user_id: int):
    return db.query(models.Cart).filter(models.Cart.user_id == user_id).first()


def add_item_to_cart(db: Session, item: schemas.CartItemCreate, user_id: int):
    # Check if the product exists and has enough stock
    product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if item.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
    
    if product.stock < item.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")

    # Get or create the user's cart
    db_cart = get_cart(db, user_id)
    if not db_cart:
        db_cart = models.Cart(user_id=user_id)
        db.add(db_cart)
        db.commit()

    # Check if the item already exists in the cart
    existing_item = db.query(models.CartItem).filter(
        models.CartItem.cart_id == db_cart.id,
        models.CartItem.product_id == item.product_id
    ).first()

    if existing_item:
        # Update quantity if item already exists
        new_quantity = existing_item.quantity + item.quantity
        if new_quantity > product.stock:
            raise HTTPException(status_code=400, detail="Not enough stock for the total quantity")
        existing_item.quantity = new_quantity
        db_item = existing_item
    else:
        # Add new item to cart
        db_item = models.CartItem(cart_id=db_cart.id, product_id=item.product_id, quantity=item.quantity)
        db.add(db_item)

    try:
        db.commit()
        db.refresh(db_item)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while adding item to cart")

    return db_item

def remove_item_from_cart(db: Session, item_id: int, user_id: int):
    db_cart = get_cart(db, user_id)
    if not db_cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    db_item = db.query(models.CartItem).filter(models.CartItem.id == item_id, models.CartItem.cart_id == db_cart.id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    db.delete(db_item)
    db.commit()
    return {"ok": True}

def update_cart_item(db: Session, item_id: int, item: schemas.CartItemCreate, user_id: int):
    db_cart = get_cart(db, user_id)
    if not db_cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    db_item = db.query(models.CartItem).filter(models.CartItem.id == item_id, models.CartItem.cart_id == db_cart.id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found in cart")
    
    if item.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
    
    product = db.query(models.Product).filter(models.Product.id == db_item.product_id).first()
    if not product or item.quantity > product.stock:
        raise HTTPException(status_code=400, detail="Not enough stock available")

    db_item.quantity = item.quantity
    db.commit()
    db.refresh(db_item)
    return db_item

def clear_cart(db: Session, user_id: int):
    db_cart = get_cart(db, user_id)
    if not db_cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    db.query(models.CartItem).filter(models.CartItem.cart_id == db_cart.id).delete()
    db.commit()
    return {"ok": True}


def get_cart_total(db: Session, user_id: int):
    db_cart = get_cart(db, user_id)
    if not db_cart:
        return 0

    total = 0
    for item in db_cart.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if product:
            total += product.price * item.quantity

    return total
