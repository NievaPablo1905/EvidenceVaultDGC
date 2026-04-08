# Evidence Vault DGC

Sistema interno de registro y gestión de evidencia digital con cadena de custodia y auditabilidad fuerte.

> **División de Intervención Remota y Análisis de Redes — Dirección General de Ciberseguridad, Policía de la Provincia de Salta.**

---

## Stack

| Componente | Tecnología                                |
|------------|-------------------------------------------|
| Backend    | Python 3.11 + FastAPI                     |
| Frontend   | React 19 + Vite + TypeScript (MVP UI)     |
| Base datos | PostgreSQL 15 (metadatos + auditoría)     |
| Storage    | MinIO (archivos de evidencia, S3-compatible) |
| Auth       | Usuarios locales, JWT (HS256)             |
| Migraciones| Alembic                                   |
| Runtime    | Docker Compose                            |

---

## Notas de seguridad

- Todos los servicios escuchan en **127.0.0.1** por defecto; el acceso es solo por VPN.
- Configurado para **HTTP** (lab interno). Aplicar TLS (nginx/Traefik) antes de exponer en redes no confiables.
- El endpoint de bootstrap (`POST /api/dev/bootstrap`) es **solo para desarrollo**; deshabilítelo poniendo `DEV_BOOTSTRAP_ENABLED=false` en producción.

---

## Inicio rápido

### 1. Clonar y configurar

```bash
git clone https://github.com/NievaPablo1905/EvidenceVaultDGC.git
cd EvidenceVaultDGC
cp .env.example .env
```

Edite `.env` y ponga valores seguros para:
- `POSTGRES_PASSWORD`
- `MINIO_ROOT_PASSWORD`
- `SECRET_KEY` → generar con `python -c "import secrets; print(secrets.token_hex(32))"`

### 2. Levantar todos los servicios (API + DB + MinIO + Web UI)

```bash
docker compose up --build -d
```

Espere a que todos los servicios estén sanos:

```bash
docker compose ps
```

Servicios disponibles:
- **Web UI:** http://localhost:3000
- **API (Swagger):** http://localhost:8000/docs
- **MinIO Console:** http://localhost:9001

### 3. Crear el primer usuario administrador (solo desarrollo)

> ⚠️ **Endpoint solo para desarrollo.** Deshabilítelo después del primer uso poniendo `DEV_BOOTSTRAP_ENABLED=false`.

**Linux/macOS:**
```bash
curl -s -X POST http://localhost:8000/api/dev/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "S3cur3P@ssw0rd!", "full_name": "Administrador"}'
```

**Windows (PowerShell):**
```powershell
$body = @{
  username  = "admin"
  password  = "S3cur3P@ssw0rd!"
  full_name = "Administrador"
} | ConvertTo-Json

Invoke-RestMethod -Method Post "http://localhost:8000/api/dev/bootstrap" `
  -ContentType "application/json" `
  -Body $body
```

### 4. Usar la interfaz web

1. Abra **http://localhost:3000** en su navegador.
2. Inicie sesión con el usuario `admin` creado en el paso anterior.
3. Desde la interfaz puede:
   - **Casos:** crear casos, ver listado.
   - **Evidencias:** dentro de cada caso, subir cualquier tipo de archivo (pdf, zip, pcap, jpg, png, log, txt, etc.), ver metadatos, descargar con verificación SHA-256.
   - **Cadena de custodia:** ver todos los eventos y ejecutar "Verificar Integridad".
4. Use el botón **Salir** para cerrar sesión.

---

## Flujo operativo

### Crear un caso
1. Haga clic en **+ Nuevo Caso**.
2. Complete título (obligatorio), descripción y base legal.
3. Confirme con **Crear Caso**.

### Subir evidencia
1. Abra el caso deseado.
2. Haga clic en **↑ Subir Evidencia**.
3. Seleccione el archivo (sin restricción de tipo).
4. Complete la descripción/fuente y la herramienta utilizada (opcional).
5. Confirme con **Subir Evidencia**.

### Descargar evidencia
- En la lista de evidencias del caso, haga clic en **↓ Descargar**.
- O abra el detalle del archivo (clic en el nombre) y use el botón de descarga.
- El sistema registra el evento de descarga en la cadena de custodia.

### Verificar integridad de la cadena
1. Vaya a la sección **Custodia**.
2. Haga clic en **✅ Verificar Integridad**.
3. El resultado mostrará si la cadena está íntegra o si hay inconsistencias.

---

## Uso via API (curl / PowerShell)

### Login y obtener token

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -d "username=admin&password=S3cur3P@ssw0rd!" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

### Crear caso

```bash
curl -s -X POST http://localhost:8000/api/cases/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Caso 2024-001", "description": "Análisis de dispositivo incautado", "legal_basis": "Ley 27411"}'
```

### Subir evidencia

```bash
curl -s -X POST http://localhost:8000/api/cases/1/evidence/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/ruta/al/archivo.pcap" \
  -F "source_description=Captura de red — dispositivo incautado ID-001" \
  -F "tool_name=tcpdump" \
  -F "tool_version=4.99.1"
```

### Descargar evidencia

```bash
curl -OJ -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/cases/1/evidence/1/download
```

El header `X-Evidence-SHA256` contiene el hash almacenado para verificación de integridad.

### Ver cadena de custodia

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/custody/ | python3 -m json.tool
```

### Verificar integridad de la cadena

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/custody/verify | python3 -m json.tool
```

### Health check

```bash
curl -s http://localhost:8000/api/health/ | python3 -m json.tool
```

---

## Roles

| Rol        | Crear caso | Subir evidencia | Descargar | Ver custodia | Verificar cadena | Crear usuarios |
|------------|:----------:|:---------------:|:---------:|:------------:|:----------------:|:--------------:|
| operator   | ✅         | ✅              | ✅        | ❌           | ❌               | ❌             |
| supervisor | ✅         | ✅              | ✅        | ✅           | ❌               | ❌             |
| auditor    | ❌         | ❌              | ✅        | ✅           | ✅               | ❌             |
| admin      | ✅         | ✅              | ✅        | ✅           | ✅               | ✅             |

---

## Documentación API

Swagger UI interactivo: `http://localhost:8000/docs`

ReDoc: `http://localhost:8000/redoc`

---

## Diseño de la cadena de custodia

Cada acción relevante agrega un registro inmutable `CustodyEvent` que contiene:

- `action` — qué sucedió (ej. `INGEST_EVIDENCE`, `DOWNLOAD_EVIDENCE`)
- `actor_id` / `actor_role` — quién realizó la acción
- `timestamp_utc` — cuándo (UTC)
- `source_ip` — IP de origen
- `prev_event_hash` — SHA-256 del evento anterior (encadenamiento por hash)
- `event_hash` — SHA-256 del JSON canónico de este evento

El endpoint `GET /api/custody/verify` recorre toda la cadena y reporta cualquier discrepancia de hash, permitiendo detectar manipulaciones.

---

## Migraciones de base de datos

Si es necesario ejecutarlas manualmente:

```bash
cd backend
alembic upgrade head
```

Las migraciones se ejecutan automáticamente al iniciar el contenedor.

---

## Estructura del proyecto

```
EvidenceVaultDGC/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── frontend/                    ← Interfaz web (React + Vite + TypeScript)
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── Layout.tsx
│       ├── api.ts               # Cliente HTTP (axios)
│       ├── components.tsx       # Componentes reutilizables
│       ├── styles.css
│       └── pages/
│           ├── Login.tsx
│           ├── Cases.tsx
│           ├── CaseDetail.tsx
│           └── Custody.tsx
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
        │   ├── config.py        # Settings desde env
        │   └── security.py      # JWT + bcrypt
        ├── db/
        │   ├── session.py       # SQLAlchemy engine/session
        │   └── models.py        # Modelos ORM
        ├── schemas/             # Schemas Pydantic
        ├── services/
        │   ├── storage.py       # Wrapper MinIO
        │   └── audit.py         # Servicio de cadena de custodia
        └── api/
            ├── deps.py          # Dependencias auth + RBAC
            └── routes/
                ├── auth.py      # POST /auth/login
                ├── dev.py       # POST /dev/bootstrap  [SOLO DEV]
                ├── users.py     # Gestión de usuarios
                ├── cases.py     # Gestión de casos
                ├── evidence.py  # Ingesta/descarga de evidencia
                ├── custody.py   # Endpoints de auditoría
                └── health.py    # GET /health/
```
