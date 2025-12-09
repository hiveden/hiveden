from typing import List

from hiveden.pkgs.models import OSType, PackageOperation, RequiredPackage


def get_all_required_packages() -> List[RequiredPackage]:
    return [
        # Storage packages
        RequiredPackage(
            name="mdadm",
            title="MDADM",
            description="Tool for managing Linux Software RAID arrays",
            operation=PackageOperation.INSTALL,
            os_types=[OSType.ALL],
            tags=["storage", "raid"]
        ),
        RequiredPackage(
            name="btrfs-progs",
            title="BTRFS Programs",
            description="Utilities for managing BTRFS filesystems",
            operation=PackageOperation.INSTALL,
            os_types=[OSType.ALL],
            tags=["storage", "filesystem"]
        ),
        RequiredPackage(
            name="parted",
            title="GNU Parted",
            description="Disk partitioning and partition resizing program",
            operation=PackageOperation.INSTALL,
            os_types=[OSType.ALL],
            tags=["storage", "disk"]
        ),
        # Example system packages (can be expanded)
        RequiredPackage(
            name="curl",
            title="cURL",
            description="Command line tool for transferring data with URLs",
            operation=PackageOperation.INSTALL,
            os_types=[OSType.ALL],
            tags=["system", "network"]
        ),
        RequiredPackage(
            name="smartmontools",
            title="smartmontools",
            description="Tool for monitoring SMART data on disks",
            operation=PackageOperation.INSTALL,
            os_types=[OSType.ALL],
            tags=["storage", "disk"]
        ),
        RequiredPackage(
            name="lxc",
            title="LXC Containers",
            description="Support for LXC",
            os_types=[OSType.ALL],
            operation=PackageOperation.INSTALL,
            tags=["lxc", "containers"]
        ),
        RequiredPackage(
            name="docker.io",
            title="Docker Containers",
            description="Support for Docker",
            os_types=[OSType.DEBIAN],
            operation=PackageOperation.INSTALL,
            tags=["docker", "containers"]
        ),
    ]
