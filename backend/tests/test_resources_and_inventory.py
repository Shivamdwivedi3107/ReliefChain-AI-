import pytest


def test_resource_and_inventory_lifecycle(client):
    # 1. Register Admin and NGO
    client.post("/api/v1/auth/register", json={"email": "admin_inv@test.com", "full_name": "Admin Inv", "password": "Password123!", "role": "admin"})
    admin_token = client.post("/api/v1/auth/login", json={"email": "admin_inv@test.com", "password": "Password123!"}).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create NGO Organization
    org_res = client.post(
        "/api/v1/organizations",
        json={
            "name": "Doctors For Humanity",
            "registration_number": "DFH-001",
            "organization_type": "NGO",
            "contact_email": "aid@dfh.org",
            "contact_phone": "+1987654321",
        },
        headers=admin_headers,
    )
    assert org_res.status_code == 201
    org_id = org_res.json()["id"]

    # 3. Create Resource Item
    res_payload = {
        "name": "Trauma Dressing Bandage Kit",
        "category": "medicine",
        "unit": "boxes",
        "description": "Sterile trauma dressings for emergency field surgeries",
    }
    res_item = client.post("/api/v1/resources", json=res_payload, headers=admin_headers)
    assert res_item.status_code == 201
    resource_id = res_item.json()["id"]

    # 4. Add Inventory Stock
    stock_payload = {
        "resource_id": resource_id,
        "quantity": 50.0,
        "warehouse_location": "Main Shelter Depot 3",
    }
    # Admin can add stock for any org
    inv_res = client.post("/api/v1/resources/inventory", json=stock_payload, headers=admin_headers)
    assert inv_res.status_code == 201
    inv_data = inv_res.json()
    assert inv_data["total_quantity"] == 50.0
    assert inv_data["available_quantity"] == 50.0

    # 5. Low-stock alerts endpoint
    alerts_res = client.get("/api/v1/resources/alerts/low-stock?threshold=60.0")
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) >= 1
    assert alerts[0]["resource_id"] == resource_id


def test_over_allocation_prevention(client):
    # Setup Admin & Org
    client.post("/api/v1/auth/register", json={"email": "admin_alloc@test.com", "full_name": "Admin Alloc", "password": "Password123!", "role": "admin"})
    admin_token = client.post("/api/v1/auth/login", json={"email": "admin_alloc@test.com", "password": "Password123!"}).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    org_res = client.post(
        "/api/v1/organizations",
        json={"name": "Water Care Network", "registration_number": "WCN-002", "organization_type": "NGO", "contact_email": "info@watercare.org", "contact_phone": "+11223344"},
        headers=admin_headers,
    )
    org_id = org_res.json()["id"]

    res_item = client.post("/api/v1/resources", json={"name": "Water Filter Units", "category": "water", "unit": "units"}, headers=admin_headers).json()
    resource_id = res_item["id"]

    # Stock 15 units
    client.post("/api/v1/resources/inventory", json={"resource_id": resource_id, "quantity": 15.0, "warehouse_location": "Depot W"}, headers=admin_headers)

    # Register Citizen & Create Request
    client.post("/api/v1/auth/register", json={"email": "cit_alloc@test.com", "full_name": "Citizen Alloc", "password": "Password123!", "role": "citizen"})
    cit_token = client.post("/api/v1/auth/login", json={"email": "cit_alloc@test.com", "password": "Password123!"}).json()["access_token"]
    cit_headers = {"Authorization": f"Bearer {cit_token}"}

    req = client.post(
        "/api/v1/relief-requests",
        json={"disaster_type": "flood", "location_name": "Zone B", "latitude": 10.0, "longitude": 20.0, "affected_people": 50},
        headers=cit_headers,
    ).json()

    # Attempt to allocate 100 units (Exceeds available 15 units -> Must fail with 400 Bad Request)
    over_res = client.post(
        "/api/v1/distributions",
        json={
            "relief_request_id": req["id"],
            "resource_id": resource_id,
            "organization_id": org_id,
            "quantity": 100.0,
            "dispatch_location": "Depot W",
        },
        headers=admin_headers,
    )
    assert over_res.status_code == 400
    res_json = over_res.json()
    err_text = res_json.get("message") or res_json.get("detail", "")
    assert "Insufficient inventory" in err_text
