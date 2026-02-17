import pytest
from unittest.mock import Mock, patch
from hiveden.storage.devices import get_system_disks, get_unused_disks
from hiveden.storage.models import Disk, Partition

# Mock raw data from lsblk
MOCK_LSBLK_DATA = [
    {
        "name": "sda",
        "path": "/dev/sda",
        "size": "500107862016",
        "model": "Samsung SSD 850",
        "serial": "S21JNSAG123456",
        "rota": False,
        "type": "disk",
        "children": [
            {
                "name": "sda1",
                "path": "/dev/sda1",
                "size": "536870912",
                "fstype": "vfat",
                "mountpoint": "/boot/efi",
            },
            {
                "name": "sda2",
                "path": "/dev/sda2",
                "size": "499570991104",
                "fstype": "ext4",
                "mountpoint": "/",
            },
        ],
    },
    {
        "name": "sdb",
        "path": "/dev/sdb",
        "size": "4000787030016",
        "model": "WD Red",
        "serial": "WD-WCC4E1234567",
        "rota": True,
        "type": "disk",
        "children": [],  # Empty disk
    },
    {
        "name": "sdc",
        "path": "/dev/sdc",
        "size": "4000787030016",
        "model": "WD Red",
        "serial": "WD-WCC4E7654321",
        "rota": True,
        "type": "disk",
        "fstype": None,
        "children": [],  # Empty disk
    },
    {
        "name": "loop0",
        "path": "/dev/loop0",
        "size": "1073741824",
        "model": None,
        "serial": None,
        "rota": False,
        "type": "loop",
        "fstype": None,
        "children": [],
    },
    {
        "name": "ram0",
        "path": "/dev/ram0",
        "size": "67108864",
        "model": None,
        "serial": None,
        "rota": False,
        "type": "disk",
        "fstype": None,
        "children": [],
    },
]


@patch("hiveden.storage.devices.get_mounts")
@patch("hiveden.storage.devices.get_raw_disks")
def test_get_system_disks_parsing(mock_get_raw, mock_get_mounts):
    mock_get_raw.return_value = MOCK_LSBLK_DATA
    mock_get_mounts.return_value = []  # Return empty mounts for simplicity

    disks = get_system_disks()

    assert len(disks) == 4

    # Check System Disk (sda)
    sda = next(d for d in disks if d.name == "sda")
    assert sda.is_system is True
    assert sda.available is False
    assert len(sda.partitions) == 2
    assert sda.model == "Samsung SSD 850"

    # Check Empty Disk (sdb)
    sdb = next(d for d in disks if d.name == "sdb")
    assert sdb.is_system is False
    assert sdb.available is True
    assert len(sdb.partitions) == 0

    # Check Loop Device (loop0) is included
    loop0 = next(d for d in disks if d.name == "loop0")
    assert loop0.is_system is False
    assert loop0.available is True

    # Check Ram Device (ram0) is excluded
    assert all(d.name != "ram0" for d in disks)


@patch("hiveden.storage.devices.get_mounts")
@patch("hiveden.storage.devices.get_raw_disks")
def test_get_unused_disks(mock_get_raw, mock_get_mounts):
    mock_get_raw.return_value = MOCK_LSBLK_DATA
    mock_get_mounts.return_value = []

    unused = get_unused_disks()

    assert len(unused) == 3
    assert all(d.name in ["sdb", "sdc", "loop0"] for d in unused)
