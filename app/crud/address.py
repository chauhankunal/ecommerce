from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from . import models, schemas

def get_shipping_address(db: Session, address_id: int, user_id: int):
    return db.query(models.ShippingAddress).filter(
        models.ShippingAddress.id == address_id,
        models.ShippingAddress.user_id == user_id
    ).first()

def create_shipping_address(db: Session, user_id: int, address_data: schemas.ShippingAddressCreate):
    address = models.ShippingAddress(
        user_id=user_id,
        street=address_data.street,
        city=address_data.city,
        state=address_data.state,
        postal_code=address_data.postal_code,
        country=address_data.country
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return address

def update_shipping_address(db: Session, address_id: int, user_id: int, address_data: schemas.ShippingAddressCreate):
    address = get_shipping_address(db, address_id, user_id)
    if not address:
        # raise ValueError("Shipping address not found or does not belong to the user.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                             detail="Shipping address not found or does not belong to the user.")
    
    address.street = address_data.street
    address.city = address_data.city
    address.state = address_data.state
    address.postal_code = address_data.postal_code
    address.country = address_data.country
    db.commit()
    db.refresh(address)
    return address

def delete_shipping_address(db: Session, address_id: int, user_id: int):
    address = get_shipping_address(db, address_id, user_id)
    if not address:
        # raise ValueError("Shipping address not found or does not belong to the user.")
        # return {"message" :"Shipping address not found or does not belong to the user." }
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                             detail="Shipping address not found or does not belong to the user.")
    
    db.delete(address)
    db.commit()
    return {"message": "Shipping address deleted successfully"}

def get_shipping_addresses(db: Session, user_id: int):
    return db.query(models.ShippingAddress).filter(models.ShippingAddress.user_id == user_id).all()
