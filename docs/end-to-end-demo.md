# ReliefChain AI — End-to-End Demonstration Narrative

This document provides a 20-step reproducible demonstration scenario for college competitions, investor presentations, and hackathon showcases.

---

## 🎭 Pre-Configured Demo Accounts

| Role | Email | Password | Primary Console |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@reliefchain.ai` | `SecurePassword123!` | Command Center & Incident Response |
| **NGO** | `ngo@reliefchain.ai` | `SecurePassword123!` | Resource Management & SPHERE Radar |
| **Volunteer** | `volunteer1@reliefchain.ai` | `SecurePassword123!` | Volunteer Ops & Delivery Scanner |
| **Citizen** | `shivam@reliefchain.ai` | `SecurePassword123!` | Citizen Emergency Hub |
| **Donor** | `donor@reliefchain.ai` | `SecurePassword123!` | Transparency Journey & Ledger |

---

## 🎬 20-Step Demonstration Workflow

1. **Start System**: Run `py -3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`.
2. **Launch Application**: Open `http://127.0.0.1:8000/ui/` in Google Chrome.
3. **Login as Citizen**: Click **Citizen** persona button or log in with `shivam@reliefchain.ai`.
4. **Trigger SOS**: Click **🚨 One-Tap Emergency SOS**.
5. **Set Location & Urgency**: Select location *"Coastal Ward 12 Shelter"*, 40 affected people, required resources: Water, Medical.
6. **Submit Request**: Click **Submit Emergency Request**.
7. **Verify AI Triage**: Observe instant priority rating (`CRITICAL`) and feature attribution breakdown.
8. **Switch to Admin Persona**: Click **Admin** persona button to switch to Command Center.
9. **View New Distress Alert**: Verify request appears in live triage feed and on Leaflet map.
10. **Declare Incident**: Click **Declare Incident** $\rightarrow$ Set severity $9.0$, affected radius $50\text{ km}$.
11. **Review AI Explanation**: Click **Explain AI Priority** to see explainable factors.
12. **SPHERE Shortage Radar**: Switch to **Resource Management** $\rightarrow$ Observe daily water & ration deficit burn rate.
13. **Volunteer Matching**: Open **Volunteer Matcher** $\rightarrow$ Run 4-factor scoring model ($96\%$ AI match for field responder).
14. **Assign Mission**: Click **Dispatch Mission** to assign responder.
15. **Switch to Volunteer Persona**: Click **Volunteer** persona pill $\rightarrow$ Accept mission.
16. **Scan Delivery QR Code**: Open single-use QR scanner $\rightarrow$ Confirm physical aid handover.
17. **Verify Burned QR**: Re-scan same QR token to demonstrate anti-fraud single-use protection.
18. **Inspect Merkle Audit Ledger**: Switch to **Ledger** tab $\rightarrow$ Verify SHA-256 block chain transaction.
19. **Interact with AI Copilot**: Open **AI Copilot** $\rightarrow$ Ask *"Summarize command center status"* $\rightarrow$ Receive telemetry-backed analysis.
20. **Generate Situation Report**: Click **Export SITREP** to generate official humanitarian summary report.
