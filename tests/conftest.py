from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.main import app

from app.config import settings
from app.database import get_db
from app.database import Base
from app.oauth2 import create_access_token
from app import models
from alembic import command
from datetime import datetime, timedelta


# SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:password123@localhost:5432/fastapi_test'
SQLALCHEMY_DATABASE_URL = f'postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}_test'


engine = create_engine(SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


@pytest.fixture()
def session():
    # print("my session fixture ran")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(session):
    def override_get_db():

        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest.fixture
def authorized_client(client):
    def _get_authorized_client(user_fixture):
        token = create_access_token({"user_id": user_fixture['id']})
        client.headers.update({
            "Authorization": f"Bearer {token}"
        })
        # client.headers = {
        #     **client.headers,
        #     "Authorization": f"Bearer {token}"
        # }
        return client
    return _get_authorized_client

@pytest.fixture
def test_user(client):
    def _create_test_user(role, user_num = 1):
        phone_number_role = {
            'CUSTOMER' : "123456789",
            'SELLER' : "234568890",
            'ADMIN' : "345678910"
        }
        user_data = {
            "user_name": f"Test {role} User",
            "email": f"{role.lower()}{user_num}@test.com",
            "phone_number": f'{phone_number_role[role]}{user_num}',
            "role": role,
            "password": "password123"
        }
        res = client.post("/users/", json=user_data)
        assert res.status_code == 201
        new_user = res.json()
        new_user['password'] = user_data['password']
        return new_user
    return _create_test_user

@pytest.fixture
def test_product_user(client):
    user_data = {
        "user_name": "Test Product User",
        "email": "product@test.com",
        "phone_number": "0000000000",
        "role": "SELLER",
        "password": "password123"
        }
    
    res = client.post("/users/", json=user_data)
    assert res.status_code == 201
    new_user = res.json()
    new_user['password'] = user_data['password']
    return new_user
    

@pytest.fixture
def test_product(session, test_product_user):    
    product_data = [{
        "name": "Classic T-Shirt",
        "description": "Comfortable cotton t-shirt for everyday wear",
        "price": 51,
        "stock": 100,
        "is_active": True,
        "category": "Apparel",
        "brand": "FashionBasics",
        "owner_id": test_product_user['id']
    }, {
        "name": "Wireless Headphones",
        "description": "High-quality wireless headphones with noise cancellation",
        "price": 199.99,
        "discount_price": 149.99,
        "sale_start_date": "2024-11-30T00:00:00Z",
        "sale_end_date": "2024-12-31T23:59:59Z",
        "stock": 50,
        "is_active": False,
        "category": "Electronics",
        "brand": "SoundMaster",
        "image_url": "https://example.com/images/wireless-headphones.jpg",
        "owner_id": test_product_user['id']
    }]
        
    def create_product_model(product):
        return models.Product(**product)

    products = list(map(create_product_model, product_data))

    session.add_all(products)
    session.commit()
    product = session.query(models.Product).all()
    return product

@pytest.fixture
def sale_product(test_product, session):
    product = test_product[0]
    product.discount_price = product.price * 0.8
    product.sale_start_date = datetime.utcnow() - timedelta(days=1)
    product.sale_end_date = datetime.utcnow() + timedelta(days=1)
    session.commit()
    return product

@pytest.fixture
def updated_product_data():
    return {
        "name": "Premium Leather Wallet",
        "description": "Handcrafted wallet made from genuine leather.",
        "price": 49.99,
        "discount_price": 39.99,
        "sale_start_date": "2024-12-10T00:00:00",
        "sale_end_date": "2024-12-20T23:59:59",
        "stock": 100,
        "is_active": True,
        "category": "Accessories",
        "brand": "LeatherCraft",
        "image_url": "https://example.com/images/premium-leather-wallet.jpg"
    }

@pytest.fixture
def test_cart(authorized_client, test_user, test_product):
    def _create_test_cart(items=None):
        customer = test_user("CUSTOMER")
        auth_client = authorized_client(customer)
        
        if items is None:
            items = [{"product_id": test_product[0].id, "quantity": 1}]
        
        cart_items = []
        for item in items:
            res = auth_client.post("/carts/items/", json=item)
            # print(res.json())
            assert res.status_code == 200
            #f"Failed to add item to cart: {res.text}"
            cart_items.append(res.json())
        
        return {"user": customer, "items": cart_items}
    
    return _create_test_cart

