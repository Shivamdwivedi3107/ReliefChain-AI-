import pytest


def test_donation_and_ledger_integration(client):
    # 1. Register Admin & Org
    client.post("/api/v1/auth/register", json={"email": "admin_don@test.com", "full_name": "Admin Don", "password": "Password123!", "role": "admin"})
    admin_token = client.post("/api/v1/auth/login", json={"email": "admin_don@test.com", "password": "Password123!"}).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    org_res = client.post(
        "/api/v1/organizations",
        json={"name": "Global Care Alliance", "registration_number": "GCA-777", "organization_type": "NGO", "contact_email": "aid@gca.org", "contact_phone": "+1999888777"},
        headers=admin_headers,
    )
    org_id = org_res.json()["id"]

    # 2. Create Monetary Donation
    don_payload = {
        "donor_name": "Alice Philanthropist",
        "donor_email": "alice@foundation.org",
        "donation_type": "monetary",
        "currency": "USD",
        "amount": 5000.0,
        "organization_id": org_id,
        "notes": "Emergency Disaster Relief Fund Contribution",
    }
    don_res = client.post("/api/v1/donations", json=don_payload)
    assert don_res.status_code == 201
    don_data = don_res.json()
    assert don_data["amount"] == 5000.0
    assert don_data["record_hash"] is not None
    assert don_data["blockchain_tx_hash"] is not None
    donation_id = don_data["id"]

    # 3. Create Resource & Physical Donation
    res_item = client.post("/api/v1/resources", json={"name": "Blankets", "category": "clothing", "unit": "pieces"}, headers=admin_headers).json()
    resource_id = res_item["id"]

    resource_don_payload = {
        "donor_name": "Bob Helper",
        "donation_type": "resource",
        "resource_id": resource_id,
        "quantity": 200.0,
        "organization_id": org_id,
    }
    res_don = client.post("/api/v1/donations", json=resource_don_payload)
    assert res_don.status_code == 201

    # 4. Check that NGO inventory was automatically incremented
    inv_list = client.get(f"/api/v1/resources/inventory/list?organization_id={org_id}", headers=admin_headers).json()
    assert len(inv_list) >= 1
    blanket_inv = next(i for i in inv_list if i["resource_id"] == resource_id)
    assert blanket_inv["available_quantity"] == 200.0

    # 5. Check Transparency Ledger endpoints (/ledger and /ledger/{id})
    ledger_res = client.get("/api/v1/ledger")
    assert ledger_res.status_code == 200
    ledger_items = ledger_res.json()["data"]
    assert len(ledger_items) >= 2

    # Get single transaction
    tx_id = ledger_items[0]["id"]
    single_tx = client.get(f"/api/v1/ledger/{tx_id}")
    assert single_tx.status_code == 200
    assert single_tx.json()["id"] == tx_id

    # 6. Verify single record against ledger (/blockchain/verify)
    verify_res = client.post(
        "/api/v1/blockchain/verify",
        json={"record_hash": don_data["record_hash"]},
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["is_verified"] == True

    # 7. Verify full ledger chain cryptographic integrity (/ledger/verify)
    chain_verify_res = client.get("/api/v1/ledger/verify")
    assert chain_verify_res.status_code == 200
    chain_data = chain_verify_res.json()
    assert chain_data["is_valid"] == True
    assert chain_data["total_blocks"] >= 2
    assert chain_data["verified_blocks"] == chain_data["total_blocks"]
