from sqlalchemy.orm import Session
from passlib.context import CryptContext

from .. import models, schemas, utils

def get_all_user(db: Session):
    return db.query(models.User).all()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_emailphone(db: Session, email: str, phone_number: str):
    return db.query(models.User).filter(models.User.email == email or models.User.phone_number == phone_number).first()

def create_user(db: Session, user: schemas.UserCreate):
    user.password = utils.hash(user.password)
        
    db_user = models.User(**user.dict())
    # print(models.UserRole.CUSTOMER, models.UserRole.ADMIN, models.UserRole.SELLER)
    # print(f"Role before insert: {db_user.role}")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user