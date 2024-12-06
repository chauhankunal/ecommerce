from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas, database

router = APIRouter(
    prefix="/users",
    tags=['Users']
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    # print("========", user.role)
    # hash the password - user.password
    db_user = crud.get_user_by_emailphone(db, email=user.email, phone_number=user.phone_number)
    if db_user:
        if db_user.email == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        elif db_user.phone_number == user.phone_number:
            raise HTTPException(status_code=400, detail="Phone Number already registered")
        else:
            raise HTTPException(status_code=400, detail="Credientials already registered")
            
    
    return crud.create_user(db=db, user=user)

@router.get('/', response_model=List[schemas.User])
def get_users(db: Session = Depends(database.get_db)):
    return crud.get_all_user(db=db)

@router.get('/{id}', response_model=schemas.User)
def get_user(id: int, db: Session = Depends(database.get_db)):
    # user = db.query(models.User).filter(models.User.id == id).first()
    user = crud.get_user(db=db, user_id=id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {id} does not exist")

    return user



