def test_register_citizen_success(client):
    payload = {
        "email": "shivam@reliefchain.ai",
        "full_name": "Shivam Dwivedi",
        "password": "SecurePassword123!",
        "role": "citizen",
        "phone_number": "+919876543210",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "shivam@reliefchain.ai"
    assert data["full_name"] == "Shivam Dwivedi"
    assert data["role"] == "citizen"
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_email_fails(client):
    payload = {
        "email": "duplicate@reliefchain.ai",
        "full_name": "User One",
        "password": "SecurePassword123!",
        "role": "citizen",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["message"]


def test_login_success_and_get_me(client):
    # 1. Register user
    reg_payload = {
        "email": "volunteer1@reliefchain.ai",
        "full_name": "Relief Volunteer",
        "password": "VolunteerPassword123!",
        "role": "volunteer",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201

    # 2. Login
    login_payload = {
        "email": "volunteer1@reliefchain.ai",
        "password": "VolunteerPassword123!",
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    token = login_data["access_token"]
    assert login_data["token_type"] == "bearer"
    assert login_data["user"]["role"] == "volunteer"

    # 3. Access /auth/me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "volunteer1@reliefchain.ai"
    assert me_data["role"] == "volunteer"


def test_login_invalid_password(client):
    reg_payload = {
        "email": "user_invalid@reliefchain.ai",
        "full_name": "Test User",
        "password": "CorrectPassword123!",
        "role": "citizen",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "user_invalid@reliefchain.ai", "password": "WrongPassword!"},
    )
    assert login_res.status_code == 401


def test_unauthorized_access_without_token(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
