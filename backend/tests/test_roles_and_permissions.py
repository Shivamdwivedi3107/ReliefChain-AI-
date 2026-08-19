import pytest


def test_role_based_access_control(client):
    # 1. Register Citizen and Login
    client.post("/api/v1/auth/register", json={"email": "regular_cit@test.com", "full_name": "Citizen User", "password": "Password123!", "role": "citizen"})
    cit_token = client.post("/api/v1/auth/login", json={"email": "regular_cit@test.com", "password": "Password123!"}).json()["access_token"]
    cit_headers = {"Authorization": f"Bearer {cit_token}"}

    # Citizen trying to create a resource item -> Must be 403 Forbidden
    res = client.post(
        "/api/v1/resources",
        json={"name": "Restricted Vaccine", "category": "medicine", "unit": "vials"},
        headers=cit_headers,
    )
    assert res.status_code == 403
    assert "Access denied" in res.json()["message"]

    # Citizen trying to dispatch distribution -> Must be 403 Forbidden
    dist_res = client.post(
        "/api/v1/distributions",
        json={"relief_request_id": "dummy", "resource_id": "dummy", "organization_id": "dummy", "quantity": 5.0},
        headers=cit_headers,
    )
    assert dist_res.status_code == 403


def test_role_aliases_registration(client):
    # Test registering with role alias 'beneficiary'
    res_ben = client.post(
        "/api/v1/auth/register",
        json={"email": "beneficiary_alias@test.com", "full_name": "Beneficiary User", "password": "Password123!", "role": "beneficiary"},
    )
    assert res_ben.status_code == 201
    assert res_ben.json()["role"] == "beneficiary"

    # Test registering with role alias 'relief_organization'
    res_ngo = client.post(
        "/api/v1/auth/register",
        json={"email": "ngo_alias@test.com", "full_name": "Relief Org User", "password": "Password123!", "role": "relief_organization"},
    )
    assert res_ngo.status_code == 201
    assert res_ngo.json()["role"] == "relief_organization"
