"""
ReliefChain AI - Comprehensive Database Seeding Script
Populates initial sample organizations, users for all roles, disasters,
resource item catalogs, depot warehouse inventories, relief requests,
donations, distributions, QR verification tokens, and Merkle ledger blocks.
"""
import sys
import os
from datetime import datetime, timezone, timedelta

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.organization import Organization
from app.models.disaster import Disaster
from app.models.resource import Resource, ResourceInventory
from app.models.relief_request import ReliefRequest
from app.models.donation import Donation
from app.models.distribution import Distribution
from app.models.qr_verification import QRVerification
from app.models.blockchain import BlockchainTransaction
from app.models.prediction import PredictionHistory
from app.models.notification import Notification
from app.services.ai_service import predict_emergency_priority
from app.services.blockchain_service import blockchain_service


def seed_database():
    print("=== Initializing ReliefChain AI Database Schema & Seed Data ===")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Check if already seeded
        existing_org = db.query(Organization).first()
        if existing_org:
            print("Database already contains records. Seeding demo accounts and ensuring baseline catalog...")

        # 2. Organizations
        org_redcross = db.query(Organization).filter(Organization.registration_number == "RC-INT-101").first()
        if not org_redcross:
            org_redcross = Organization(
                name="Red Cross Disaster Response",
                registration_number="RC-INT-101",
                organization_type="NGO",
                contact_email="emergency@redcross-relief.org",
                contact_phone="+1-800-555-0199",
                address="450 Humanitarian Way, District 1",
                verification_status="verified",
                is_active=True,
            )
            db.add(org_redcross)
            db.commit()
            db.refresh(org_redcross)

        org_unicef = db.query(Organization).filter(Organization.registration_number == "UN-AID-202").first()
        if not org_unicef:
            org_unicef = Organization(
                name="UN Children's Emergency Aid",
                registration_number="UN-AID-202",
                organization_type="International NGO",
                contact_email="aid@un-relief.org",
                contact_phone="+1-800-555-0244",
                address="100 Global Peace Plaza",
                verification_status="verified",
                is_active=True,
            )
            db.add(org_unicef)
            db.commit()
            db.refresh(org_unicef)

        # 3. Users for all 5 Roles (Admin, NGO, Volunteer, Citizen, Donor)
        default_pwd = get_password_hash("SecurePassword123!")

        users_data = [
            {"email": "admin@reliefchain.ai", "full_name": "System Administrator", "role": "admin", "org": None},
            {"email": "ngo@reliefchain.ai", "full_name": "Sarah Connor (Red Cross)", "role": "ngo", "org": org_redcross.id},
            {"email": "volunteer1@reliefchain.ai", "full_name": "John Field Volunteer", "role": "volunteer", "org": org_redcross.id},
            {"email": "shivam@reliefchain.ai", "full_name": "Shivam Dwivedi", "role": "citizen", "org": None},
            {"email": "donor@reliefchain.ai", "full_name": "Global Hope Foundation", "role": "donor", "org": None},
        ]

        for u_data in users_data:
            existing = db.query(User).filter(User.email == u_data["email"]).first()
            if not existing:
                user = User(
                    email=u_data["email"],
                    full_name=u_data["full_name"],
                    hashed_password=default_pwd,
                    role=u_data["role"],
                    organization_id=u_data["org"],
                    is_active=True,
                    is_verified=True,
                )
                db.add(user)
        db.commit()

        # 4. Disasters
        disasters_data = [
            {
                "title": "Monsoon Flash Flood Sector 7",
                "disaster_type": "flood",
                "severity": "high",
                "status": "active",
                "location_name": "Riverbend Basin, North Zone",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "radius_km": 15.0,
                "description": "Severe flooding with submerged arterial roads and stranded residential pockets.",
            },
            {
                "title": "Coastal Cyclone Warning Cat-3",
                "disaster_type": "cyclone",
                "severity": "critical",
                "status": "active",
                "location_name": "Eastern Coastal Bay",
                "latitude": 19.8135,
                "longitude": 85.8312,
                "radius_km": 40.0,
                "description": "High velocity wind gusts and tidal surges disrupting power and potable water.",
            },
        ]

        for d_data in disasters_data:
            existing_disaster = db.query(Disaster).filter(Disaster.title == d_data["title"]).first()
            if not existing_disaster:
                disaster = Disaster(**d_data)
                db.add(disaster)
        db.commit()

        flood_disaster = db.query(Disaster).filter(Disaster.disaster_type == "flood").first()

        # 5. Resource Item Catalog
        resources_data = [
            {"name": "Potable Drinking Water (20L Cans)", "category": "water", "unit": "cans", "description": "Purified drinking water for hydration in flooded zones."},
            {"name": "Trauma & Burn Surgical Dressing Kit", "category": "medicine", "unit": "boxes", "description": "Emergency medical supplies for field paramedics."},
            {"name": "High-Calorie Ready-to-Eat Rations", "category": "food", "unit": "cartons", "description": "Non-perishable meal kits for displaced families."},
            {"name": "Heavy-Duty Weatherproof Tents", "category": "shelter", "unit": "kits", "description": "Modular 6-person temporary shelter kits."},
            {"name": "Water Purification Chemical Tablets", "category": "water", "unit": "strips", "description": "Disinfectant chlorine tablets for untreated water."},
            {"name": "Thermal Emergency Blankets", "category": "clothing", "unit": "units", "description": "Insulated reflective blankets for hypothermia prevention."},
        ]

        created_resources = []
        for r_data in resources_data:
            existing_res = db.query(Resource).filter(Resource.name == r_data["name"]).first()
            if not existing_res:
                res = Resource(**r_data)
                db.add(res)
                db.commit()
                db.refresh(res)
                created_resources.append(res)
            else:
                created_resources.append(existing_res)

        # 6. Warehouse Inventories for Red Cross
        for r in created_resources:
            inv = db.query(ResourceInventory).filter(
                ResourceInventory.organization_id == org_redcross.id,
                ResourceInventory.resource_id == r.id,
            ).first()
            if not inv:
                qty = 250.0 if r.category == "water" else (100.0 if r.category == "medicine" else 150.0)
                inv = ResourceInventory(
                    organization_id=org_redcross.id,
                    resource_id=r.id,
                    total_quantity=qty,
                    available_quantity=qty,
                    reserved_quantity=0.0,
                    warehouse_location="Red Cross Central Logistics Hub",
                )
                db.add(inv)
        db.commit()

        # 7. Sample Initial Relief Requests
        citizen_user = db.query(User).filter(User.email == "shivam@reliefchain.ai").first()
        volunteer_user = db.query(User).filter(User.email == "volunteer1@reliefchain.ai").first()

        existing_req = db.query(ReliefRequest).first()
        if not existing_req:
            # Critical Flood Request
            pred_priority, conf, factors = predict_emergency_priority(
                disaster_type="flood",
                affected_people=45,
                location_risk_score=7.0,
                food_needed=1,
                water_needed=1,
                medical_needed=1,
                vulnerable_population=1,
            )

            sample_req = ReliefRequest(
                citizen_id=citizen_user.id,
                disaster_id=flood_disaster.id if flood_disaster else None,
                disaster_type="flood",
                location_name="Riverbend Sector 4, Community Hall",
                latitude=28.6145,
                longitude=77.2095,
                affected_people=45,
                required_resources=[{"item": "trauma medical kit", "qty": 5}, {"item": "potable water", "qty": 40}],
                urgency_description="Water level rising rapidly. 8 elderly citizens and 4 infants require immediate trauma care and clean water.",
                priority=pred_priority,
                status="assigned",
                assigned_organization_id=org_redcross.id,
                assigned_volunteer_id=volunteer_user.id,
                ai_predicted_priority=pred_priority,
                ai_confidence=conf,
                ai_factors=factors,
            )
            db.add(sample_req)
            db.commit()
            db.refresh(sample_req)

            # Sample Distribution
            water_res = created_resources[0]
            crypto_qr_token = "token-relief-demo-proof-2026"
            sample_dist = Distribution(
                relief_request_id=sample_req.id,
                resource_id=water_res.id,
                organization_id=org_redcross.id,
                volunteer_id=volunteer_user.id,
                recipient_id=citizen_user.id,
                quantity=20.0,
                status="dispatched",
                dispatch_location="Red Cross Central Logistics Hub",
                delivery_latitude=28.6145,
                delivery_longitude=77.2095,
                qr_token=crypto_qr_token,
                record_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            )
            db.add(sample_dist)
            db.commit()
            db.refresh(sample_dist)

            # QR Verification record
            qr_ver = QRVerification(
                distribution_id=sample_dist.id,
                verification_token=crypto_qr_token,
                status="valid",
            )
            db.add(qr_ver)

            # Initial Ledger Block
            bc_tx = BlockchainTransaction(
                event_type="distribution",
                reference_id=sample_dist.id,
                record_hash=sample_dist.record_hash,
                previous_hash="0000000000000000000000000000000000000000000000000000000000000000",
                tx_hash="0x7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
                block_number=1001,
                status="confirmed",
            )
            db.add(bc_tx)
            sample_dist.blockchain_tx_hash = bc_tx.tx_hash
            db.commit()

        print("=== Database Seeding Completed Successfully! ===")
        print("Demo accounts available:")
        print("  • Admin:     admin@reliefchain.ai     (Password: SecurePassword123!)")
        print("  • NGO:       ngo@reliefchain.ai       (Password: SecurePassword123!)")
        print("  • Volunteer: volunteer1@reliefchain.ai (Password: SecurePassword123!)")
        print("  • Citizen:   shivam@reliefchain.ai    (Password: SecurePassword123!)")
        print("  • Donor:     donor@reliefchain.ai     (Password: SecurePassword123!)")

    except Exception as err:
        db.rollback()
        print(f"Seeding error: {err}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
