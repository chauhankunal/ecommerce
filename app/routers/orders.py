from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas, models, oauth2, database

router = APIRouter(
    prefix="/orders",
    tags=['Order']
)

@router.post("/", response_model=schemas.Order)
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    allowed_roles = [models.UserRole.CUSTOMER]  # Only customers can place orders
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to place orders"
        )
    
    # Fetch cart
    cart = crud.get_cart(db, user_id=current_user.id)
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Validate shipping address
    selected_address = crud.get_shipping_address(db, address_id=order.shipping_address_id, user_id=current_user.id)
    if not selected_address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The selected shipping address does not exist or does not belong to you."
        )
    
    # Create order
    try:
        db_order = crud.create_order(
            db=db,
            user_id=current_user.id,
            shipping_address_id=order.shipping_address_id,
            cart_items=cart.items,
        )
        crud.clear_cart(db=db, user_id=current_user.id)  # Clear cart after order creation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return db_order


@router.get("/", response_model=List[schemas.Order])
def get_orders(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role == models.UserRole.CUSTOMER:
        # Customers only see their own orders
        return crud.get_user_orders(db=db, user_id=current_user.id)
    elif current_user.role == models.UserRole.SELLER:
        # Sellers see orders for their products
        return crud.get_seller_orders(db=db, seller_id=current_user.id)
    elif current_user.role == models.UserRole.ADMIN:
        # Admins can view all orders
        return crud.get_all_orders(db=db)
    else:
        raise HTTPException(status_code=403, detail="Invalid role")
    
@router.get("/{order_id}", response_model=schemas.Order)
def get_order_by_id(
    order_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # Fetch the order by ID
    order = crud.get_order(db=db, order_id=order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Role-based access control
    if current_user.role == models.UserRole.CUSTOMER:
        # Customers can only view their own orders
        if order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own orders"
            )
    
    # Sellers and Admins can view any order
    if current_user.role == models.UserRole.SELLER:
        # Check if the seller is associated with the order's product
        if not crud.is_seller_related_to_order(db=db, user_id=current_user.id, order_id=order_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view orders related to your products"
            )
    
    if current_user.role == models.UserRole.ADMIN:
        # Admins can view all orders
        pass

    return order


@router.patch("/{order_id}/status", response_model=schemas.Order)
def update_order_status(
    order_id: int,
    order_status: schemas.OrderStatusUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
    ):
    # Only sellers or admins can update order status
    if current_user.role not in [models.UserRole.SELLER, models.UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update order status"
        )

    # Get the order
    order = crud.get_order(db=db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Sellers can only update orders related to their products
    if current_user.role == models.UserRole.SELLER:
        if not crud.is_seller_related_to_order(db=db, user_id=current_user.id, order_id=order_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update orders related to your products"
            )

    # Update order status
    try:
        updated_order = crud.update_order_status(db=db, order_id=order_id, new_status=order_status.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return updated_order

@router.patch("/{order_id}/cancel", response_model=schemas.Order)
def cancel_order(
    order_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # Fetch the order
    order = crud.get_order(db=db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Role-based permissions
    if current_user.role == models.UserRole.CUSTOMER:
        if order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own orders"
            )
    elif current_user.role not in [models.UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to cancel this order"
        )
    
    # Business logic: Only certain statuses can be canceled
    if order.status not in [models.OrderStatus.PENDING, models.OrderStatus.PROCESSING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status {order.status}. Only 'PENDING' or 'PROCESSING' orders can be canceled."
        )
    
    # Cancel the order
    try:
        updated_order = crud.cancel_order(db=db, order_id=order_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return updated_order

