from fastapi import FastAPI

from hiveden.api.routers import config, docker, info, lxc, shares

app = FastAPI(
    title="Hiveden API",
    description="An API for managing your personal server.",
    version="0.1.0",
)

app.include_router(config.router)
app.include_router(docker.router)
app.include_router(info.router)
app.include_router(lxc.router)
app.include_router(shares.router)

