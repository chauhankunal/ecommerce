from app import crud

def test_read_cart(authorized_client, test_cart):
    cart = test_cart()
    auth_client = authorized_client(cart["user"])
    res = auth_client.get("/carts/")
    assert res.status_code == 200
    assert len(res.json()["items"]) == len(cart["items"])
    
def test_read_nonexistent_cart(authorized_client, test_user):
    customer = test_user("CUSTOMER")
    res = authorized_client(customer).get("/carts/")
    assert res.status_code == 404
    assert res.json()["detail"] == "Cart not found"

def test_read_empty_cart(authorized_client, test_cart, session):
    cart = test_cart()
    # Clear the cart
    crud.clear_cart(db=session, user_id=cart["user"]["id"])
    
    res = authorized_client(cart["user"]).get("/carts/")
    assert res.status_code == 200
    assert res.json()["items"] == []

def test_add_multiple_items_to_cart(authorized_client, test_cart, test_product):
    items = [
        {"product_id": test_product[0].id, "quantity": 2},
        {"product_id": test_product[1].id, "quantity": 1}
    ]
    cart = test_cart(items)
    assert len(cart["items"]) == 2
    auth_client = authorized_client(cart["user"])
    res = auth_client.get("/carts/")
    assert res.status_code == 200
    assert len(res.json()["items"]) == 2

def test_remove_item_from_cart(authorized_client, test_cart):
    cart = test_cart()
    item_id = cart["items"][0]["id"]
    auth_client = authorized_client(cart["user"])
    res = auth_client.delete(f"/carts/items/{item_id}")
    assert res.status_code == 204

    # Verify item was removed
    res = auth_client.get("/carts/")
    assert res.status_code == 200
    assert len(res.json()["items"]) == 0
    
def test_update_cart_item(authorized_client, test_cart):
    cart = test_cart()
    item_id = cart["items"][0]["id"]
    update_data = {"quantity": 3}
    res = authorized_client(cart["user"]).put(f"/carts/items/{item_id}", json=update_data)
    assert res.status_code == 200
    assert res.json()["quantity"] == 3
    
def test_clear_cart(authorized_client, test_cart):
    cart = test_cart()
    auth_client = authorized_client(cart["user"])
    res = auth_client.delete("/carts/clear/")
    assert res.status_code == 204

    # Verify that the cart is empty
    get_res = auth_client.get("/carts/")
    assert get_res.status_code == 200
    assert get_res.json()["items"] == []

def test_get_cart_total(authorized_client, test_cart):
    cart = test_cart([
        {"product_id": 1, "quantity": 2},
        {"product_id": 2, "quantity": 1}
    ])
    res = authorized_client(cart["user"]).get("/carts/amount/")
    assert res.status_code == 200
    assert "Total price for your cart is" in res.text