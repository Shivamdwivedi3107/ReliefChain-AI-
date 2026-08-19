def test_create_and_query_relief_request(client):
    # 1. Register Citizen
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "citizen@test.com", "full_name": "Test Citizen", "password": "Password123!", "role": "citizen"},
    )
    assert reg.status_code == 201
    
    # 2. Login
    login = client.post("/api/v1/auth/login", json={"email": "citizen@test.com", "password": "Password123!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Relief Request (Severe flood with medical trauma)
    req_payload = {
        "disaster_type": "flood",
        "location_name": "Riverbend Sector 4",
        "latitude": 28.5355,
        "longitude": 77.3910,
        "affected_people": 25,
        "required_resources": [{"item": "trauma medical kit", "qty": 5}, {"item": "potable drinking water", "qty": 100}],
        "urgency_description": "Severe flooding, medical trauma reported with elderly citizens stranded.",
    }
    create_res = client.post("/api/v1/relief-requests", json=req_payload, headers=headers)
    assert create_res.status_code == 201
    req_data = create_res.json()
    assert req_data["priority"] in ["critical", "high"]
    assert req_data["ai_predicted_priority"] in ["critical", "high"]
    assert req_data["status"] == "pending"

    # 4. List requests
    list_res = client.get("/api/v1/relief-requests")
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1
