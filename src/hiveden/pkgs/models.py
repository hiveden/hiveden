from enum import Enum
from pydantic import BaseModel

class PackageOperation(str, Enum):
    INSTALL = "INSTALL"
    UNINSTALL = "UNINSTALL"

class RequiredPackage(BaseModel):
    name: str
    title: str
    description: str
    operation: PackageOperation = PackageOperation.INSTALL

class PackageStatus(RequiredPackage):
    installed: bool
