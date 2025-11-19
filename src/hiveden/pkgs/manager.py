from hiveden.hwosinfo.os import get_os_info
from hiveden.pkgs.arch import ArchPackageManager
from hiveden.pkgs.debian import DebianPackageManager
from hiveden.pkgs.fedora import FedoraPackageManager


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
