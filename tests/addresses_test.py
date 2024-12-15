import pytest
from app import schemas

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

# Test creating a shipping address
def test_create_shipping_address(authorized_client, test_user):
    customer = test_user("CUSTOMER")
    address_data = {
        "street": "123 Test St",
        "city": "Test City",
        "state": "Test State",
        "country": "Test Country",
        "postal_code": "12345"
    }
    res = authorized_client(customer).post("/shipping-addresses/", json=address_data)
    assert res.status_code == 201
    assert res.json()["street"] == address_data["street"]
    assert res.json()["user_id"] == customer["id"]

# Test creating a shipping address as a non-customer (should fail)
def test_create_shipping_address_as_seller(authorized_client, test_user):
    seller = test_user("SELLER")
    address_data = {
        "street": "123 Test St",
        "city": "Test City",
        "state": "Test State",
        "country": "Test Country",
        "postal_code": "12345"
    }
    res = authorized_client(seller).post("/shipping-addresses/", json=address_data)
    assert res.status_code == 403
    assert "Only customers can create shipping addresses" in res.json()["detail"]

# Test getting all shipping addresses
def test_get_all_shipping_addresses(authorized_client, test_user):
    customer = test_user("CUSTOMER")
    # Create two addresses
    create_test_address(authorized_client, customer)
    create_test_address(authorized_client, customer)
    
    res = authorized_client(customer).get("/shipping-addresses/")
    assert res.status_code == 200
    assert len(res.json()) == 2

# Test getting a specific shipping address
def test_get_specific_shipping_address(authorized_client, test_user):
    customer = test_user("CUSTOMER")
    address = create_test_address(authorized_client, customer)
    
    res = authorized_client(customer).get(f"/shipping-addresses/{address['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == address["id"]

# Test getting a non-existent shipping address
def test_get_non_existent_shipping_address(authorized_client, test_user):
    customer = test_user("CUSTOMER")
    res = authorized_client(customer).get("/shipping-addresses/99999")
    assert res.status_code == 404

# Test updating a shipping address
def test_update_shipping_address(authorized_client, test_user):
    customer = test_user("CUSTOMER")
    address = create_test_address(authorized_client, customer)
    
    update_data = {
        "street": "456 New St",
        "city": "New City",
        "state": "New State",
        "country": "New Country",
        "postal_code": "67890"
    }
    res = authorized_client(customer).put(f"/shipping-addresses/{address['id']}", json=update_data)
    assert res.status_code == 200
    assert res.json()["street"] == update_data["street"]

# Test updating a non-existent shipping address
def test_update_non_existent_shipping_address(authorized_client, test_user):
    customer = test_user("CUSTOMER")
    update_data = {
        "street": "456 New St",
        "city": "New City",
        "state": "New State",
        "country": "New Country",
        "postal_code": "67890"
    }
    res = authorized_client(customer).put("/shipping-addresses/99999", json=update_data)
    assert res.status_code == 404

# Test deleting a shipping address
def test_delete_shipping_address(authorized_client, test_user):
    customer = test_user("CUSTOMER")
    address = create_test_address(authorized_client, customer)
    
    res = authorized_client(customer).delete(f"/shipping-addresses/{address['id']}")
    assert res.status_code == 200
    assert res.json()["message"] == "Shipping address deleted successfully"

    # Verify the address is deleted
    res = authorized_client(customer).get(f"/shipping-addresses/{address['id']}")
    assert res.status_code == 404

# Test deleting a non-existent shipping address
def test_delete_non_existent_shipping_address(authorized_client, test_user):
    customer = test_user("CUSTOMER")
    res = authorized_client(customer).delete("/shipping-addresses/99999")
    assert res.status_code == 404

# Test that a user can't access another user's shipping address
def test_cant_access_other_users_address(authorized_client, test_user):
    customer1 = test_user("CUSTOMER")
    customer2 = test_user("CUSTOMER", 2)
    
    address = create_test_address(authorized_client, customer1)
    
    res = authorized_client(customer2).get(f"/shipping-addresses/{address['id']}")
    assert res.status_code == 404

