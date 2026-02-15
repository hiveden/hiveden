from fastapi import APIRouter
from hiveden.api.routers.docker import containers, images, volumes

router = APIRouter(prefix="/docker")

# Include container routes directly
router.include_router(containers.router)

# Include image routes
router.include_router(images.router)

# Include volume routes
router.include_router(volumes.router)
