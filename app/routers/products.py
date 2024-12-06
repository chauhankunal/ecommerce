from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional

from .. import schemas, models, oauth2, crud, database

router = APIRouter(
    prefix="/products",
    tags=['Products']
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Product)
def create_product(
    product: schemas.ProductCreate, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.get_current_user)
    ):
    
    if current_user.role not in [models.UserRole.SELLER, models.UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform this action")
    print(type(current_user.id))
    data = crud.create_product(db=db, product=product, owner_id=current_user.id)
    return data

@router.put("/{id}", status_code = status.HTTP_200_OK ,response_model=schemas.Product)
def update_product(
    id: int, 
    product_update: schemas.ProductUpdate, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.get_current_user)
    ):
    db_product = crud.get_product(db, id)
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with id: {id} does not exist")

    if current_user.role == models.UserRole.SELLER and db_product.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this product")
    elif current_user.role not in [models.UserRole.ADMIN, models.UserRole.SELLER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update products")

    try:
        updated_product = crud.update_product(db, db_product, product_update)
        return updated_product
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[schemas.Product])
def get_all_products(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    db: Session = Depends(database.get_db)
    ):
    products = crud.get_products(db, skip=skip, limit=limit, include_inactive=include_inactive)
    if not products:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="No products found")
    return products

@router.get("/search", response_model=List[schemas.Product])
def search_products(
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_active: Optional[bool] = None,
    on_sale: Optional[bool] = Query(None, description="Filter for products currently on sale"),
    db: Session = Depends(database.get_db)
    ):
    
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=400, detail="Invalid price range: min_price cannot be greater than max_price")
    
    products = crud.search_products(db, category, brand, min_price, max_price, is_active, on_sale)
    if not products:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No products found matching the criteria.")
    return products

@router.get("/{id}", response_model=schemas.Product)
def get_product_by_id(
    id: int = Path(..., gt=0),
    db: Session = Depends(database.get_db)
    ):
    product = crud.get_product(db, id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    id: int, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.get_current_user)
    ):
    db_product = crud.get_product(db, id)
    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Product with id: {id} does not exist"
        )
    
    if db_product.owner_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to perform requested action"
        )
    
    try:
        crud.delete_product(db, db_product)
        return {"message": "Product deleted successfully"}
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An error occurred while deleting the product"
        )

