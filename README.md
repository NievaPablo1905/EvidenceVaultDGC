# Evidence Vault DGC

Sistema interno de registro y gestión de evidencia digital con cadena de custodia y auditabilidad fuerte.

> **División de Intervención Remota y Análisis de Redes — Dirección General de Ciberseguridad, Policía de la Provincia de Salta.**

---

## Stack

| Component  | Technology                                |
|------------|-------------------------------------------|
| Backend    | Python 3.11 + FastAPI                     |
| Database   | PostgreSQL 15 (metadata + audit log)      |
| Storage    | MinIO (evidence blobs, S3-compatible)     |
| Auth       | Local users, JWT (HS256)                  |
| Migrations | Alembic                                   |
| Runtime    | Docker Compose                            |

---

## Security notes

- All services bind to **127.0.0.1** by default; access via VPN only.
- Currently configured for **HTTP** (internal lab). Apply TLS termination (nginx/Traefik) before exposing over any untrusted network.
- The bootstrap endpoint (`POST /api/dev/bootstrap`) is **dev-only**; disable it by setting `DEV_BOOTSTRAP_ENABLED=false` in production.

---

## Quickstart

### 1. Clone & configure

```bash
git clone https://github.com/NievaPablo1905/EvidenceVaultDGC.git
cd EvidenceVaultDGC
cp .env.example .env
```

Edit `.env` and set strong values for:
- `POSTGRES_PASSWORD`
- `MINIO_ROOT_PASSWORD`
- `SECRET_KEY` → generate with `python -c "import secrets; print(secrets.token_hex(32))"`

### 2. Start services

```bash
docker compose up --build -d
```

Wait for all services to be healthy:

```bash
docker compose ps
```

### 3. Bootstrap the first admin user

> ⚠️ **Dev-only endpoint.** Disable after first use by setting `DEV_BOOTSTRAP_ENABLED=false`.

```bash
curl -s -X POST http://localhost:8000/api/dev/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "S3cur3P@ssw0rd!", "full_name": "Administrador"}'
```

### 4. Log in and obtain a token

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -d "username=admin&password=S3cur3P@ssw0rd!" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token: $TOKEN"
```

### 5. Create a case

```bash
curl -s -X POST http://localhost:8000/api/cases/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Caso 2024-001", "description": "Análisis de dispositivo incautado", "legal_basis": "Ley 27411 / Art. 309 sexies CPPN"}'
```

### 6. Upload evidence

```bash
curl -s -X POST http://localhost:8000/api/cases/1/evidence/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/evidence.pcap" \
  -F "source_description=Captura de red — dispositivo incautado ID-001" \
  -F "tool_name=tcpdump" \
  -F "tool_version=4.99.1"
```

### 7. Download evidence (logs custody event)

```bash
curl -OJ -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/cases/1/evidence/1/download
```

The response header `X-Evidence-SHA256` contains the stored hash for integrity verification.

### 8. View chain-of-custody log

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/custody/ | python3 -m json.tool
```

### 9. Verify chain integrity (auditor/admin)

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/custody/verify | python3 -m json.tool
```

### 10. Health check

```bash
curl -s http://localhost:8000/api/health/ | python3 -m json.tool
```

---

## Roles

| Role       | Create case | Upload evidence | Download | View custody log | Verify chain | Create users |
|------------|:-----------:|:---------------:|:--------:|:----------------:|:------------:|:------------:|
| operator   | ✅          | ✅              | ✅       | ❌               | ❌           | ❌           |
| supervisor | ✅          | ✅              | ✅       | ✅               | ❌           | ❌           |
| auditor    | ❌          | ❌              | ✅       | ✅               | ✅           | ❌           |
| admin      | ✅          | ✅              | ✅       | ✅               | ✅           | ✅           |

---

## API Documentation

Interactive Swagger UI available at: `http://localhost:8000/docs`

ReDoc: `http://localhost:8000/redoc`

---

## Chain-of-Custody design

Every significant action appends an immutable `CustodyEvent` record containing:

- `action` — what happened (e.g., `INGEST_EVIDENCE`, `DOWNLOAD_EVIDENCE`)
- `actor_id` / `actor_role` — who performed the action
- `timestamp_utc` — when (UTC)
- `source_ip` — originating IP address
- `prev_event_hash` — SHA-256 of the previous event (hash chaining)
- `event_hash` — SHA-256 of this event's canonical JSON

The `GET /api/custody/verify` endpoint walks the entire chain and reports any hash mismatches, enabling detection of tampering.

---

## Database migrations

Run manually if needed:

```bash
cd backend
alembic upgrade head
```

Migrations are run automatically on container start.

---

## Project structure

```
EvidenceVaultDGC/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── alembic.ini
    ├── alembic/
    │   ├── env.py
    │   └── versions/
    │       └── 001_initial_schema.py
    └── app/
        ├── main.py
        ├── core/
        │   ├── config.py        # Settings from env
        │   └── security.py      # JWT + bcrypt
        ├── db/
        │   ├── session.py       # SQLAlchemy engine/session
        │   └── models.py        # ORM models
        ├── schemas/             # Pydantic schemas
        ├── services/
        │   ├── storage.py       # MinIO wrapper
        │   └── audit.py         # Chain-of-custody service
        └── api/
            ├── deps.py          # Auth dependencies + RBAC
            └── routes/
                ├── auth.py      # POST /auth/login
                ├── dev.py       # POST /dev/bootstrap  [DEV ONLY]
                ├── users.py     # User management
                ├── cases.py     # Case management
                ├── evidence.py  # Evidence ingest/download
                ├── custody.py   # Audit log endpoints
                └── health.py    # GET /health/
```
