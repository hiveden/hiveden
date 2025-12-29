import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hiveden.api.routers import (
    config,
    docker,
    explorer,
    info,
    lxc,
    pkgs,
    shares,
    shell,
    storage,
    system,
)
from hiveden.db.session import get_db_manager

app = FastAPI(
    title="Hiveden API",
    description="Hiveden API",
)

# Initialize Database on Startup
@app.on_event("startup")
def startup_db():
    db_manager = get_db_manager()
    db_manager.initialize_db()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(config.router)
app.include_router(docker.router)
app.include_router(info.router)
app.include_router(lxc.router)
app.include_router(shares.router)
app.include_router(shell.router)
app.include_router(pkgs.router)
app.include_router(storage.router)
app.include_router(explorer.router)
app.include_router(system.router)
