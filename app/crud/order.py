from sqlalchemy.orm import Session
# from sqlalchemy.exc import IntegrityError

from . import models, schemas

def get_shipping_address(db: Session, address_id: int, user_id: int):
    return db.query(models.ShippingAddress).filter(
        models.ShippingAddress.id == address_id,
        models.ShippingAddress.user_id == user_id
    ).first()
    
def calculate_discounted_price(product_price: float, discount: float) -> float:
    """
    Calculate the final price after applying a discount.
    :param product_price: Original price of the product
    :param discount: Discount percentage (e.g., 20 for 20%)
    :return: Discounted price
    """
    if discount is not None and discount > 0:
        return round(product_price - (product_price * (discount / 100)), 2)
    return product_price

def create_order(db: Session, user_id: int, shipping_address_id: int, cart_items: list):
    # Verify shipping address
    shipping_address = get_shipping_address(db, address_id=shipping_address_id, user_id=user_id)
    if not shipping_address:
        raise ValueError("Invalid shipping address")
    
    total_price = 0.0
    order_items = []
    
    try:
        # Begin atomic transaction
        # with db.begin():
        # Step 1: Pre-validate stock for all products
        for item in cart_items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if not product:
                raise ValueError(f"Product with ID {item.product_id} does not exist.")
            if product.stock < item.quantity:
                raise ValueError(f"Insufficient stock for product {item.product_id}. Available: {product.stock}, Requested: {item.quantity}")

        # Step 2: Deduct stock and prepare order items
        for item in cart_items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
                
            # Deduct stock
            product.stock -= item.quantity
            db.add(product)  # Save stock update to the database
                
            # Calculate discounted price
            discounted_price = calculate_discounted_price(product_price=product.price, discount=product.discount_price)
            total_price += discounted_price * item.quantity

            # Create OrderItem object
            order_item = models.OrderItem(
                product_id=item.product_id,
                quantity=item.quantity,
                price=discounted_price,
            )
            order_items.append(order_item)

        # Step 3: Create the order
        order = models.Order(
            user_id=user_id,
            shipping_address_id=shipping_address_id,
            total_price=total_price,
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # Step 4: Add the order items to the database
        for order_item in order_items:
            order_item.order_id = order.id
            db.add(order_item)

        db.commit()
        db.refresh(order)

        return order

    except ValueError as e:
        # Handle validation errors gracefully
        db.rollback()  # Rollback the transaction to maintain consistency
        raise ValueError(str(e))


def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()

def update_order_status(db: Session, order_id: int, new_status: str):
    order = get_order(db=db, order_id=order_id)
    if not order:
        raise ValueError("Order not found")
    order.status = new_status
    db.commit()
    db.refresh(order)
    return order

def get_seller_orders(db: Session, seller_id: int):
    return db.query(models.Order).join(models.OrderItem).join(models.Product).filter(
        models.Product.owner_id == seller_id
    ).all()

def get_all_orders(db: Session):
    return db.query(models.Order).all()

def is_seller_related_to_order(db: Session, user_id: int, order_id: int):
    return db.query(models.Order).join(models.OrderItem).join(models.Product).filter(
        models.Product.owner_id == user_id,
        models.Order.id == order_id
    ).count() > 0

def get_user_orders(db: Session, user_id: int):
    return db.query(models.Order).filter(models.Order.user_id == user_id).all()

def clear_cart(db: Session, user_id: int):
    cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
    if cart:
        db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete()
        db.commit()

def cancel_order(db: Session, order_id: int):
    order = get_order(db=db, order_id=order_id)
    if not order:
        raise ValueError("Order not found")

    # Update the order status
    order.status = models.OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)

    # Optional: Restock products
    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity
            db.add(product)

    db.commit()
    return order
