from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session
from datetime import datetime

from .. import database, schemas, models, oauth2, utils
import jwt

router = APIRouter(tags=['Authentication'])


@router.post('/login/', response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):

    user = db.query(models.User).filter(
        models.User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

    # create a token
    # return token
    access_token = oauth2.create_access_token(data={"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout/")
async def logout(token: str = Depends(oauth2.oauth2_scheme), db: Session = Depends(database.get_db)):
    # Extract expiry from the token if available
    try:
        payload = jwt.decode(token, oauth2.SECRET_KEY, algorithms=[oauth2.ALGORITHM])
        expiry_time = payload.get("exp")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Create a blacklist entry in the database
    blacklisted_token = models.TokenBlacklist(
        token=token,
        expiry_time=datetime.utcfromtimestamp(expiry_time)  # Store token's expiry
    )
    db.add(blacklisted_token)
    db.commit()

    return {"msg": "Successfully logged out"}

