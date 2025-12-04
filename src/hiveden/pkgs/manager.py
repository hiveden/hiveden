from typing import List, Optional
from hiveden.hwosinfo.os import get_os_info
from hiveden.pkgs.arch import ArchPackageManager
from hiveden.pkgs.debian import DebianPackageManager
from hiveden.pkgs.fedora import FedoraPackageManager
from hiveden.pkgs.models import PackageStatus, OSType
from hiveden.pkgs.registry import get_all_required_packages


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


def get_system_required_packages(tags: Optional[str] = None) -> List[PackageStatus]:
    pm = get_package_manager()
    os_info = get_os_info()
    
    # Map current OS to OSType enum
    current_distro_id = os_info.get('id', 'unknown').lower()
    
    # Map of common distro IDs to our OSType enum
    distro_map = {
        "arch": OSType.ARCH,
        "debian": OSType.DEBIAN,
        "ubuntu": OSType.UBUNTU,
        "fedora": OSType.FEDORA,
        "centos": OSType.CENTOS,
        "rhel": OSType.RHEL
    }
    
    current_os_type = distro_map.get(current_distro_id)
    
    # Get all registered packages
    all_packages = get_all_required_packages()
    
    # Filter by OS
    os_filtered_packages = []
    for pkg in all_packages:
        if OSType.ALL in pkg.os_types:
            os_filtered_packages.append(pkg)
        elif current_os_type and current_os_type in pkg.os_types:
            os_filtered_packages.append(pkg)
            
    # Filter by tags if provided
    final_packages = []
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        
    if not tag_list:
        final_packages = os_filtered_packages
    else:
        for pkg in os_filtered_packages:
            # Check if package has ANY of the requested tags
            if any(tag in pkg.tags for tag in tag_list):
                final_packages.append(pkg)
    
    return [
        PackageStatus(
            name=pkg.name,
            title=pkg.title,
            description=pkg.description,
            operation=pkg.operation,
            os_types=pkg.os_types,
            tags=pkg.tags,
            installed=pm.is_installed(pkg.name)
        )
        for pkg in final_packages
    ]
