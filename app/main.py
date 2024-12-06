from fastapi import FastAPI
from.routers import users, products, auth, carts, orders, addresses
from . import models
from .database import engine
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(carts.router)
app.include_router(orders.router)
app.include_router(addresses.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the E-commerce API"}



