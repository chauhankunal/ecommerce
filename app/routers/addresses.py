from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, models, oauth2, crud, database

router = APIRouter(
    prefix="/shipping-addresses",
    tags=["Shipping Address"]
)

# GET /shipping-addresses/: Fetch all shipping addresses for the current user.
# GET /shipping-addresses/{address_id}: Fetch a specific shipping address.
# POST /shipping-addresses/: Create a new shipping address for the current user.
# PUT /shipping-addresses/{address_id}: Update an existing shipping address for the current user.
# DELETE /shipping-addresses/{address_id}: Delete a shipping address

@router.get("/", response_model=List[schemas.ShippingAddress])
def get_shipping_addresses(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # Fetch all shipping addresses for the current user
    return crud.get_shipping_addresses(db=db, user_id=current_user.id)

@router.get("/{address_id}", response_model=schemas.ShippingAddress)
def get_shipping_address(
    address_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    address = crud.get_shipping_address(db=db, address_id=address_id, user_id=current_user.id)
    if not address:
        raise HTTPException(status_code=404, detail="Shipping address not found.")
    return address

@router.post("/", status_code= status.HTTP_201_CREATED, response_model=schemas.ShippingAddress)
def create_shipping_address(
    address: schemas.ShippingAddressCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    
    if current_user.role != models.UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create shipping addresses"
        )
    # Create a new shipping address for the current user
    new_address = crud.create_shipping_address(db=db, user_id=current_user.id, address_data=address)
    return new_address

@router.put("/{address_id}", response_model=schemas.ShippingAddress)
def update_shipping_address(
    address_id: int,
    address: schemas.ShippingAddressCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # Update an existing shipping address for the current user
    updated_address = crud.update_shipping_address(db=db, address_id=address_id, user_id=current_user.id, address_data=address)
    return updated_address

@router.delete("/{address_id}", response_model=dict)
def delete_shipping_address(
    address_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # Delete the specified shipping address for the current user
    response = crud.delete_shipping_address(db=db, address_id=address_id, user_id=current_user.id)
    return response
