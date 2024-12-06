from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, oauth2, models, crud, database

router = APIRouter(
    prefix="/carts",
    tags=['Cart']
)


@router.get("/", response_model=schemas.Cart)
def read_cart(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    db_cart = crud.get_cart(db, user_id=current_user.id)
    if db_cart is None:
        raise HTTPException(status_code=404, detail="Cart not found")
    return db_cart

@router.post("/items/", response_model=schemas.CartItem)
def add_to_cart(item: schemas.CartItemCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role in [models.UserRole.SELLER, models.UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sellers are not allowed to create carts or place orders"
        )
    return crud.add_item_to_cart(db=db, item=item, user_id=current_user.id)

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item_from_cart(item_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    return crud.remove_item_from_cart(db=db, item_id=item_id, user_id=current_user.id)

@router.put("/items/{item_id}", response_model=schemas.CartItem)
def update_cart_item(item_id: int, item: schemas.CartItemUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    return crud.update_cart_item(db=db, item_id=item_id, item=item, user_id=current_user.id)

@router.delete("/clear/", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    return crud.clear_cart(db=db, user_id=current_user.id)

@router.get("/amount/", status_code=status.HTTP_200_OK)
def get_cart_total(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    return f"Total price for your cart is {crud.get_cart_total(db=db, user_id=current_user.id)}"


# {
#     "product_id" : 10
#     "quantity" : 2
# }