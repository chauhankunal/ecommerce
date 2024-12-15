import pytest
from app import schemas, models

# Helper function to create a shipping address
def create_test_address(authorized_client, user):
    address_data = {
        "street": "123 Test St",
        "city": "Test City",
        "state": "Test State",
        "country": "Test Country",
        "postal_code": "12345"
    }
    res = authorized_client(user).post("/shipping-addresses/", json=address_data)
    assert res.status_code == 201
    return res.json()

# Helper function to create a cart with items
def create_test_cart(authorized_client, user, test_product):
    item = {"product_id": test_product[0].id, "quantity": 2}
    res = authorized_client(user).post("/carts/items/", json=item)
    assert res.status_code == 200
    return res.json()

# Test creating an order
def test_create_order(authorized_client, test_user, test_product, test_cart):
    customer = test_user("CUSTOMER")
    address = create_test_address(authorized_client, customer)
    cart = create_test_cart(authorized_client, customer, test_product)
    
    order_data = {"shipping_address_id": address["id"]}
    res = authorized_client(customer).post("/orders/", json=order_data)
    assert res.status_code == 200
    assert "id" in res.json()
    assert res.json()["shipping_address_id"] == address["id"]

# Test creating an order with empty cart
def test_create_order_empty_cart(authorized_client, test_user):
    customer = test_user("CUSTOMER")
    address = create_test_address(authorized_client, customer)
    
    order_data = {"shipping_address_id": address["id"]}
    res = authorized_client(customer).post("/orders/", json=order_data)
    
    assert res.status_code == 400
    assert "Cart is empty" in res.json()["detail"]


# Test getting orders as a customer
def test_get_orders_as_customer(authorized_client, test_user, test_product, test_cart):
    customer = test_user("CUSTOMER")
    address = create_test_address(authorized_client, customer)
    cart = create_test_cart(authorized_client, customer, test_product)
    
    # Create an order
    order_data = {"shipping_address_id": address["id"]}
    authorized_client(customer).post("/orders/", json=order_data)
    
    # Get orders
    res = authorized_client(customer).get("/orders/")
    assert res.status_code == 200
    assert len(res.json()) > 0
    # ToDo need to implement the joins to have user_id in order response 
    # assert res.json()[0]["user_id"] == customer["id"] 

# Test getting orders as a seller
def test_get_orders_as_seller(authorized_client, test_user, test_product_user, test_product, test_cart):
    customer = test_user("CUSTOMER")
    seller = test_product_user
    address = create_test_address(authorized_client, customer)
    cart = create_test_cart(authorized_client, customer, test_product)
    
    # Create an order
    order_data = {"shipping_address_id": address["id"]}
    authorized_client(customer).post("/orders/", json=order_data)
    
    # Get orders as seller
    res = authorized_client(seller).get("/orders/")
    assert res.status_code == 200
    assert len(res.json()) > 0

# Test getting orders as an admin
def test_get_orders_as_admin(authorized_client, test_user, test_product, test_cart):
    customer = test_user("CUSTOMER")
    admin = test_user("ADMIN")
    address = create_test_address(authorized_client, customer)
    cart = create_test_cart(authorized_client, customer, test_product)
    
    # Create an order
    order_data = {"shipping_address_id": address["id"]}
    authorized_client(customer).post("/orders/", json=order_data)
    
    # Get orders as admin
    res = authorized_client(admin).get("/orders/")
    assert res.status_code == 200
    assert len(res.json()) > 0

# Test getting a specific order by ID
def test_get_order_by_id(authorized_client, test_user, test_product, test_cart):
    customer = test_user("CUSTOMER")
    address = create_test_address(authorized_client, customer)
    cart = create_test_cart(authorized_client, customer, test_product)
    
    # Create an order
    order_data = {"shipping_address_id": address["id"]}
    create_res = authorized_client(customer).post("/orders/", json=order_data)
    order_id = create_res.json()["id"]
    
    # Get the order
    res = authorized_client(customer).get(f"/orders/{order_id}")
    assert res.status_code == 200
    assert res.json()["id"] == order_id

# Test getting a non-existent order
def test_get_non_existent_order(authorized_client, test_user):
    customer = test_user("CUSTOMER")
    res = authorized_client(customer).get("/orders/99999")
    assert res.status_code == 404

# Test updating order status as a seller
def test_update_order_status_as_seller(authorized_client, test_user, test_product_user, test_product, test_cart):
    customer = test_user("CUSTOMER")
    seller = test_product_user
    address = create_test_address(authorized_client, customer)
    cart = create_test_cart(authorized_client, customer, test_product)
    
    # Create an order
    order_data = {"shipping_address_id": address["id"]}
    create_res = authorized_client(customer).post("/orders/", json=order_data)
    order_id = create_res.json()["id"]
    
    # Update order status
    status_update = {"status": "PROCESSING"}
    res = authorized_client(seller).patch(f"/orders/{order_id}/status", json=status_update)
    assert res.status_code == 200
    assert res.json()["status"] == "PROCESSING"

# Test updating order status as a customer (should fail)
def test_update_order_status_as_customer(authorized_client, test_user, test_product, test_cart):
    customer = test_user("CUSTOMER")
    address = create_test_address(authorized_client, customer)
    cart = create_test_cart(authorized_client, customer, test_product)
    
    # Create an order
    order_data = {"shipping_address_id": address["id"]}
    create_res = authorized_client(customer).post("/orders/", json=order_data)
    order_id = create_res.json()["id"]
    
    # Try to update order status
    status_update = {"status": "PROCESSING"}
    res = authorized_client(customer).patch(f"/orders/{order_id}/status", json=status_update)
    assert res.status_code == 403

# Test cancelling an order as a customer
def test_cancel_order_as_customer(authorized_client, test_user, test_product, test_cart):
    customer = test_user("CUSTOMER")
    address = create_test_address(authorized_client, customer)
    cart = create_test_cart(authorized_client, customer, test_product)
    
    # Create an order
    order_data = {"shipping_address_id": address["id"]}
    create_res = authorized_client(customer).post("/orders/", json=order_data)
    order_id = create_res.json()["id"]
    
    # Cancel the order
    res = authorized_client(customer).patch(f"/orders/{order_id}/cancel")
    assert res.status_code == 200
    assert res.json()["status"] == "CANCELLED"

# Test cancelling an order that's already shipped (should fail)
def test_cancel_shipped_order(authorized_client, test_user, test_product_user, test_product, test_cart):
    customer = test_user("CUSTOMER")
    seller = test_product_user
    address = create_test_address(authorized_client, customer)
    cart = create_test_cart(authorized_client, customer, test_product)
    
    # Create an order
    order_data = {"shipping_address_id": address["id"]}
    create_res = authorized_client(customer).post("/orders/", json=order_data)
    order_id = create_res.json()["id"]
    
    # Update order status to SHIPPED
    status_update = {"status": "SHIPPED"}
    authorized_client(seller).patch(f"/orders/{order_id}/status", json=status_update)
    
    # Try to cancel the order
    res = authorized_client(customer).patch(f"/orders/{order_id}/cancel")
    assert res.status_code == 400
    assert "Cannot cancel order with status SHIPPED" in res.json()["detail"]

# Test cancelling another user's order (should fail)
def test_cancel_other_users_order(authorized_client, test_user, test_product, test_cart):
    customer1 = test_user("CUSTOMER")
    customer2 = test_user("CUSTOMER", 2)
    address = create_test_address(authorized_client, customer1)
    cart = create_test_cart(authorized_client, customer1, test_product)
    
    # Create an order for customer1
    order_data = {"shipping_address_id": address["id"]}
    create_res = authorized_client(customer1).post("/orders/", json=order_data)
    order_id = create_res.json()["id"]
    
    # Try to cancel the order as customer2
    res = authorized_client(customer2).patch(f"/orders/{order_id}/cancel")
    assert res.status_code == 403
