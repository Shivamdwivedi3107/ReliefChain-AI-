# ReliefChain AI — Production Security & Governance

This document details the multi-layered security controls, threat mitigations, and compliance practices implemented across ReliefChain AI.

---

## 1. Authentication & Session Management

- **Password Hashing**: Implemented via bcrypt with cost factor 12 (`bcrypt.gensalt(rounds=12)`).
- **JWT Architecture**: Standard JSON Web Tokens signed with HS256 algorithm and enforced claims:
  - `sub`: User ID / Email
  - `role`: Role entitlement (`citizen`, `volunteer`, `ngo`, `donor`, `admin`)
  - `exp`: Strict token expiration timestamp (default: 24 hours)
  - `iat` / `nbf`: Issued-at and not-before cryptographic timestamps
- **Secret Key Enforcement**: Production mode rejects default or weak secrets (< 32 characters) on startup.

---

## 2. Role-Based Access Control (RBAC) Matrix

| Endpoint Group | Citizen | Volunteer | NGO | Donor | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| `POST /api/v1/relief-requests` (SOS) | ✅ | ❌ | ❌ | ❌ | ✅ |
| `GET /api/v1/relief-requests` | Own / Masked | Assigned | Org-Scoped | Read-Only | Full Access |
| `POST /api/v1/inventory/restock` | ❌ | ❌ | ✅ | ❌ | ✅ |
| `POST /api/v1/distributions/dispatch` | ❌ | ❌ | ✅ | ❌ | ✅ |
| `POST /api/v1/qr/verify` | ❌ | ✅ | ✅ | ❌ | ✅ |
| `GET /api/v1/audit-logs` | ❌ | ❌ | ❌ | ❌ | ✅ |
| `POST /api/v1/ai/reload-model` | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 3. Network & Transport Security

- **OWASP Security Headers**:
  - `X-Content-Type-Options: nosniff` (prevents MIME confusion attacks)
  - `X-Frame-Options: DENY` (mitigates clickjacking attacks)
  - `Referrer-Policy: strict-origin-when-cross-origin` (prevents token/URL leaking)
  - `X-XSS-Protection: 1; mode=block`
- **Trusted Host Middleware**: Blocks HTTP Host header spoofing attacks by whitelisting valid domains.
- **CORS Whitelisting**: Strict origin matching in production; wildcards (`*`) are rejected.
- **Rate Limiting**: Sliding window per-IP quotas protect login, registration, and SOS intake endpoints against brute-force and DDoS attacks.

---

## 4. File Upload & Photographic Evidence Security

- **Path Traversal Protection**: Uploaded filenames are sanitized and stored under UUID-based paths.
- **MIME Whitelist Filtering**: Strict verification rejecting disallowed executables or scripts (`.php`, `.sh`, `.exe`, `.py`).
- **File Size Caps**: 10MB per upload hard limit enforced in FastAPI and 15MB buffer limit in Nginx reverse proxy.
- **SHA-256 Checksumming**: Every intake computes a cryptographic digest linked to immutable audit logs.
