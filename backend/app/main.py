from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, cases, custody, dev, evidence, health, users

app = FastAPI(
    title="Evidence Vault DGC",
    description=(
        "Internal evidence registry for the División de Intervención Remota y Análisis de Redes — "
        "Dirección General de Ciberseguridad, Policía de la Provincia de Salta. "
        "Provides chain-of-custody, SHA-256 hash verification, and role-based access control."
    ),
    version="0.1.0",
)

# Allow VPN-internal origins; tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # NOTE: restrict to internal VPN range in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api"

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(dev.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(cases.router, prefix=API_PREFIX)
app.include_router(evidence.router, prefix=API_PREFIX)
app.include_router(custody.router, prefix=API_PREFIX)
