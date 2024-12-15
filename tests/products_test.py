import pytest
from app import schemas, models
from datetime import datetime, timedelta

# Authentication is not required here because the endpoint is publicly accessible. 
# Anyone can fetch the data without needing to be authorized.
def test_get_all_active_product(client, test_product):
    res = client.get("/products/")
    def validate(product):
        return schemas.Product(**product)
    product_list = list(map(validate, res.json()))
    active_products = [p for p in test_product if p.is_active]
    assert len(res.json()) == len(active_products)
    assert res.status_code == 200
    
    for i in active_products:
        assert i.is_active == True #checking is_active flag because it is true by default
            
def test_get_product_by_id(client, test_product):
    res = client.get(f'products/{test_product[0].id}')
    product = schemas.Product(**res.json())
    assert product.name == test_product[0].name
    assert res.status_code == 200
  
@pytest.mark.parametrize("id, status_code, error_type", [
    ("abc", 422, "int_parsing"),
    (0, 422, "greater_than"),
    (-1, 422, "greater_than"),
    (2.5, 422, "int_parsing"),
    (999999, 404, "not_found")
])
def test_invalid_product_id(client, id, status_code, error_type):
    res = client.get(f"/products/{id}")
    assert res.status_code == status_code

    if status_code == 422:
        error_detail = res.json()["detail"]
        assert isinstance(error_detail, list)
        assert len(error_detail) > 0
        assert "id" in error_detail[0]["loc"]
        
        if error_type == "int_parsing":
            assert "integer" in error_detail[0]["msg"].lower()
        elif error_type == "greater_than":
            assert "greater than" in error_detail[0]["msg"].lower()
    elif status_code == 404:
        assert "not found" in res.json()["detail"].lower()

@pytest.mark.parametrize("role, expected_status", [
    ("CUSTOMER", 403),
    ("SELLER", 201),
    ("ADMIN", 201)
])
def test_create_product_by_role(authorized_client, test_user, role, expected_status):
    data = {"name": "Test Product", "price": 100, "stock": 10, "category": "Test", "brand": "Test"}
    user = test_user(role)
    auth_client = authorized_client(user)
    res = auth_client.post(
        "/products/",
        json=data
    )
    assert res.status_code == expected_status
    if role == "CUSTOMER":
        assert res.json()["detail"] == "Not authorized to perform this action"
    else:
        assert res.json()["name"] == data["name"]
        assert res.json()["category"] == data["category"]
        assert res.json()["brand"] == data["brand"]
 
def test_unauthorized_user_create_product(client):
    data = {"name": "Test Product", "price": 100, "stock": 10, "category": "Test", "brand": "Test"}
    res = client.post(
        f'products/', 
        json=data)
    assert res.json()['detail'] == "Not authenticated"
    assert  res.status_code ==  401
    
def test_unauthorized_user_delete_product(client, test_product):
    res = client.delete(f'/products/{test_product[0].id}')
    assert res.json()['detail'] == "Not authenticated"
    assert  res.status_code ==  401    
    
def test_customer_cannot_delete_product(authorized_client, test_user, test_product):
    customer_user = test_user('CUSTOMER')
    auth_client = authorized_client(customer_user)
    res = auth_client.delete(f'/products/{test_product[0].id}')
    assert res.json()['detail'] == "Not authorized to perform requested action"
    assert  res.status_code ==  403
    
def test_seller_cannot_delete_others_product(authorized_client, test_user, test_product):
    seller_user = test_user('SELLER')
    auth_client = authorized_client(seller_user)
    res = auth_client.delete(f'/products/{test_product[0].id}')
    assert res.json()['detail'] == "Not authorized to perform requested action"
    assert  res.status_code ==  403
    
def test_seller_can_delete_own_product(session, authorized_client, test_product_user, test_product):

    auth_client = authorized_client(test_product_user)
    id = test_product[0].id
    res = auth_client.delete(f'/products/{id}')
    assert  res.status_code ==  204
    deleted_product = session.query(models.Product).filter(models.Product.id == id).first()
    assert deleted_product is None
    
def test_admin_can_delete_any_product(session, authorized_client, test_user, test_product):

    admin_user = test_user('ADMIN')
    auth_client = authorized_client(admin_user)
    id = test_product[1].id
    res = auth_client.delete(f'/products/{id}')
    assert  res.status_code ==  204
    deleted_product = session.query(models.Product).filter(models.Product.id == id).first()
    assert deleted_product is None
    
def test_delete_non_exist_product(authorized_client, test_user):
    admin_user = test_user('ADMIN')
    auth_client = authorized_client(admin_user)
    res = auth_client.delete("/products/1000000000")
    assert res.json()['detail'] == "Product with id: 1000000000 does not exist"
    assert res.status_code == 404
    
def test_unauthorized_user_update_product(client, test_product, updated_product_data):
    res = client.put(f"/products/{test_product[0].id}",
                     json = updated_product_data)
    assert res.json()['detail'] == "Not authenticated"
    assert  res.status_code ==  401 
    
def test_customer_cannot_update_product(authorized_client, test_user, test_product, updated_product_data):
    customer_user = test_user('CUSTOMER')
    auth_client = authorized_client(customer_user)
    res = auth_client.put(f"/products/{test_product[0].id}",
                     json = updated_product_data)
    assert res.json()['detail'] == "Not authorized to update products"
    assert  res.status_code ==  403
    
def test_seller_cannot_update_others_product(authorized_client, test_user, test_product, updated_product_data):
    seller_user = test_user('SELLER')
    auth_client = authorized_client(seller_user)
    res = auth_client.put(f'/products/{test_product[0].id}',
                             json = updated_product_data)
    assert res.json()['detail'] == "Not authorized to update this product"
    assert  res.status_code ==  403

def test_seller_can_update_own_product(session, authorized_client, test_product_user, test_product, updated_product_data):
    auth_client = authorized_client(test_product_user)
    id = test_product[0].id
    res = auth_client.put(f'/products/{id}',
                          json = updated_product_data)
    assert  res.status_code ==  200
    updated_data = session.query(models.Product).filter(models.Product.id == id).first()
    assert updated_data.name == updated_product_data['name']
    assert updated_data.description == updated_product_data['description']
    assert updated_data.price == updated_product_data['price']
    assert updated_data.discount_price == updated_product_data['discount_price']
    assert updated_data.stock == updated_product_data['stock']
    assert updated_data.category == updated_product_data['category']
    assert updated_data.is_active == updated_product_data['is_active']
    assert updated_data.brand == updated_product_data['brand']
    assert updated_data.image_url == updated_product_data['image_url']
    
        
def test_admin_can_delete_any_product(session, authorized_client, test_user, test_product):

    updated_product = {
        "name": "ADMIN Premium Leather Wallet",
        "description": " ADMIN Handcrafted wallet made from genuine leather.",
        "price": 500,
        "discount_price": 309,
        "sale_start_date": "2024-12-10T00:00:00",
        "sale_end_date": "2024-12-20T23:59:59",
        "stock": 190,
        "is_active": True,
        }
    admin_user = test_user("ADMIN")
    auth_client = authorized_client(admin_user)
    id = test_product[0].id
    res = auth_client.put(f'/products/{id}',
                          json = updated_product)
    assert  res.status_code ==  200
    updated_data = session.query(models.Product).filter(models.Product.id == id).first()
    assert updated_data.name == updated_product['name']
    assert updated_data.description == updated_product['description']
    assert updated_data.price == updated_product['price']
    assert updated_data.discount_price == updated_product['discount_price']
    assert updated_data.stock == updated_product['stock']
    assert updated_data.is_active == updated_product['is_active']

def test_search_products_no_params(client, test_product):
    res = client.get("/products/search")
    assert res.status_code == 200
    assert len(res.json()) == len(test_product)

def test_search_products_by_category(client, test_product):
    category = test_product[0].category
    res = client.get(f"/products/search?category={category}")
    assert res.status_code == 200
    assert all(product['category'] == category for product in res.json())

def test_search_products_by_brand(client, test_product):
    brand = test_product[0].brand
    res = client.get(f"/products/search?brand={brand}")
    assert res.status_code == 200
    assert all(product['brand'] == brand for product in res.json())

def test_search_products_by_price_range(client, test_product):
    min_price = 50
    max_price = 200
    res = client.get(f"/products/search?min_price={min_price}&max_price={max_price}")
    assert res.status_code == 200
    assert all(min_price <= product['price'] <= max_price for product in res.json())

def test_search_products_active_only(client, test_product):
    res = client.get("/products/search?is_active=true")
    assert res.status_code == 200
    assert all(product['is_active'] for product in res.json())

def test_search_products_on_sale(client, test_product):
    res = client.get("/products/search?on_sale=true")
    assert res.status_code == 200
    assert all(product['discount_price'] is not None for product in res.json())

def test_search_products_combined_params(client, test_product):
    category = test_product[0].category
    brand = test_product[0].brand
    min_price = 50
    max_price = 200
    res = client.get(f"/products/search?category={category}&brand={brand}&min_price={min_price}&max_price={max_price}&is_active=true")
    assert res.status_code == 200
    for product in res.json():
        assert product['category'] == category
        assert product['brand'] == brand
        assert min_price <= product['price'] <= max_price
        assert product['is_active']

def test_search_products_no_results(client):
    res = client.get("/products/search?category=NonExistentCategory")
    assert res.status_code == 404
    assert res.json()['detail'] == "No products found matching the criteria."

def test_search_products_on_sale_date_range(client, sale_product):
    res = client.get("/products/search?on_sale=true")
    assert res.status_code == 200
    assert len(res.json()) > 0
    assert all(product['discount_price'] is not None for product in res.json())

def test_search_products_case_insensitive(client, test_product):
    category = test_product[0].category.lower()
    res = client.get(f"/products/search?category={category}")
    assert res.status_code == 200
    assert len(res.json()) > 0

def test_search_products_partial_match(client, test_product):
    partial_brand = test_product[0].brand[:3]
    res = client.get(f"/products/search?brand={partial_brand}")
    assert res.status_code == 200
    assert len(res.json()) > 0

def test_search_products_invalid_price_range(client):
    res = client.get("/products/search?min_price=200&max_price=100")
    assert res.status_code == 400
    assert res.json()['detail'] == "Invalid price range: min_price cannot be greater than max_price"

