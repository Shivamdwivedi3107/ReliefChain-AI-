# ReliefChain AI — Security Architecture & Hardening Policies

## 1. Threat Model & Security Principles
ReliefChain AI adheres to the principle of least privilege, defense-in-depth, and human-in-the-loop operational oversight.

---

## 2. Authentication & Cryptography
- **Stateless JWT Tokens**: Signed using HMAC-SHA256 (`HS256`). Subject claims include user ID and assigned role. Tokens expire after 24 hours (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).
- **Password Hashing**: Bcrypt with salted rounds. Passwords are never stored in plaintext.
- **Merkle Ledger**: Sequential SHA-256 block chain linkage ensures tamper-evident auditability of all disaster relief transactions.
- **Proof-of-Delivery Nonce**: One-time cryptographic verification tokens are burned upon delivery scan to eliminate duplicate aid claims.

---

## 3. Role-Based Access Control (RBAC)
Endpoint permissions are strictly enforced via FastAPI dependencies:
- **`citizen`**: Create emergency SOS requests, view own distress tickets, locate evacuation shelters.
- **`volunteer`**: Accept assigned missions, view workload capacity meters, scan single-use delivery QR codes.
- **`ngo`**: Manage warehouse depot balances, allocate supply bundles, submit SITREPs.
- **`donor`**: Access public verifiable transparency journeys and blockchain transaction receipts.
- **`admin`**: Full Command Center authority, threat grid escalations, AI model activation, disaster simulation sandbox.

---

## 4. Operational Hardening & Guards
- **Secret Key Validation**: Production settings strictly reject secrets under 32 characters or default development keys.
- **CORS Whitelisting**: Wildcard origins (`*`) are disallowed in production mode.
- **Rate Limiting**: Sliding-window IP rate limiting (Login: 15/min, Register: 10/min, Public: 120/min).
- **Log Masking**: Passwords, tokens, and database credentials are automatically masked in structured JSON logs.
- **Correlation ID**: Every HTTP request receives an `X-Request-ID` header propagated across logs for end-to-end tracing.

---

## 5. Human-in-the-Loop Emergency Disclaimer
> [!IMPORTANT]
> AI priority scoring and volunteer recommendation engines operate as decision-support tools. Final operational and life-safety authority remains exclusively with human incident commanders and certified first responders.
