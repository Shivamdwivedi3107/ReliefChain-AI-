def test_full_distribution_and_qr_verification_loop(client):
    # 1. Register Admin
    client.post("/api/v1/auth/register", json={"email": "admin@test.com", "full_name": "Admin", "password": "Password123!", "role": "admin"})
    admin_token = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "Password123!"}).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create Organization
    org_res = client.post(
        "/api/v1/organizations",
        json={
            "name": "Red Cross Emergency",
            "registration_number": "RC-101",
            "organization_type": "NGO",
            "contact_email": "aid@redcross.org",
            "contact_phone": "+123456789",
        },
        headers=admin_headers,
    )
    org_id = org_res.json()["id"]

    # 3. Create Resource & Add Inventory
    res_item = client.post(
        "/api/v1/resources",
        json={"name": "Water Purification Tabs", "category": "water", "unit": "boxes"},
        headers=admin_headers,
    ).json()
    resource_id = res_item["id"]

    client.post(
        "/api/v1/resources/inventory",
        json={"resource_id": resource_id, "quantity": 100.0, "warehouse_location": "Depot 1"},
        headers=admin_headers,
    )

    # 4. Register Citizen & Create Request
    client.post("/api/v1/auth/register", json={"email": "citizen2@test.com", "full_name": "Citizen Two", "password": "Password123!", "role": "citizen"})
    cit_token = client.post("/api/v1/auth/login", json={"email": "citizen2@test.com", "password": "Password123!"}).json()["access_token"]
    cit_headers = {"Authorization": f"Bearer {cit_token}"}

    req = client.post(
        "/api/v1/relief-requests",
        json={
            "disaster_type": "earthquake",
            "location_name": "Shelter Zone A",
            "latitude": 34.0522,
            "longitude": -118.2437,
            "affected_people": 10,
            "urgency_description": "Clean water required",
        },
        headers=cit_headers,
    ).json()
    request_id = req["id"]

    # 5. Dispatch Distribution (Locks 10 units of inventory)
    dist_res = client.post(
        "/api/v1/distributions",
        json={
            "relief_request_id": request_id,
            "resource_id": resource_id,
            "organization_id": org_id,
            "quantity": 10.0,
            "dispatch_location": "Depot 1",
        },
        headers=admin_headers,
    )
    assert dist_res.status_code == 201
    dist_data = dist_res.json()
    dist_id = dist_data["id"]
    qr_token = dist_data["qr_token"]
    assert dist_data["status"] == "dispatched"

    # 6. Generate QR Code image
    qr_gen = client.post(f"/api/v1/qr/generate/{dist_id}")
    assert qr_gen.status_code == 200
    assert "data:image/png;base64" in qr_gen.json()["qr_code_image_base64"]

    # 7. Validate QR token via GET
    qr_check = client.get(f"/api/v1/qr/verify/{qr_token}")
    assert qr_check.status_code == 200
    assert qr_check.json()["is_valid"] == True

    # 8. Volunteer confirms delivery
    confirm_res = client.post(
        "/api/v1/qr/confirm",
        json={"verification_token": qr_token, "latitude": 34.0525, "longitude": -118.2435},
        headers=admin_headers,
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "verified"

    # 9. Verify subsequent attempt is rejected (double claim prevention)
    double_claim = client.post(
        "/api/v1/qr/confirm",
        json={"verification_token": qr_token},
        headers=admin_headers,
    )
    assert double_claim.status_code == 400
