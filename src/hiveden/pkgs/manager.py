from typing import List
from hiveden.hwosinfo.os import get_os_info
from hiveden.pkgs.arch import ArchPackageManager
from hiveden.pkgs.debian import DebianPackageManager
from hiveden.pkgs.fedora import FedoraPackageManager
from hiveden.pkgs.models import PackageStatus


def get_package_manager():
    os_info = get_os_info()
    distro = os_info.get('id')
    if distro in ["arch"]:
        return ArchPackageManager()
    elif distro in ["debian", "ubuntu"]:
        return DebianPackageManager()
    elif distro in ["fedora", "centos", "rhel"]:
        return FedoraPackageManager()
    else:
        raise Exception(f"Unsupported distribution: {distro}")


def get_system_required_packages() -> List[PackageStatus]:
    pm = get_package_manager()
    packages = pm.get_required_packages()
    return [
        PackageStatus(
            name=pkg.name,
            title=pkg.title,
            description=pkg.description,
            operation=pkg.operation,
            installed=pm.is_installed(pkg.name)
        )
        for pkg in packages
    ]
