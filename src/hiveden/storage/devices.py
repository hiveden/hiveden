from typing import List
from hiveden.hwosinfo.hw import get_disks as get_raw_disks, get_mounts
from hiveden.storage.models import Disk, Partition, MountPoint


def flatten_mounts(mounts_list):
    """Helper to flatten the nested tree from findmnt."""
    flat = []
    for m in mounts_list:
        flat.append(m)
        if "children" in m:
            flat.extend(flatten_mounts(m["children"]))
    return flat


def get_system_disks() -> List[Disk]:
    """
    Retrieves system disks and parses them into Disk models.
    Determines availability based on partitions and mount points.
    """
    raw_data = get_raw_disks()

    # Get and flatten mount info
    raw_mounts = get_mounts()
    all_mounts = flatten_mounts(raw_mounts)

    # Map device path -> list of mount info dicts
    mount_map = {}
    for m in all_mounts:
        src = m.get("source")
        if not src:
            continue
        # Clean up source to find real device path (e.g. /dev/sda1[/@home] -> /dev/sda1)
        real_dev = src.split("[")[0]
        if real_dev not in mount_map:
            mount_map[real_dev] = []
        mount_map[real_dev].append(m)

    disks = []

    for device in raw_data:
        # Skip ram disks
        if device.get("name", "").startswith("ram"):
            continue

        # Parse partitions
        partitions = []
        is_system = False

        # lsblk nests partitions under 'children'
        raw_partitions = device.get("children", [])

        raid_group = None
        raid_level = None

        def find_raid_info(children):
            """Recursively search for RAID devices in children."""
            nonlocal raid_group, raid_level
            for child in children:
                # Check if this child is a RAID device
                child_type = child.get("type", "")
                if (
                    child_type == "raid1"
                    or child_type == "raid5"
                    or child_type == "raid0"
                    or child_type == "raid6"
                    or child_type == "raid10"
                ):
                    raid_group = child.get("name")
                    raid_level = child_type
                    return

                # Check for md device by name convention if type isn't explicit
                if child.get("name", "").startswith("md"):
                    raid_group = child.get("name")
                    # Often lsblk type for md devices is 'raidX' but if not found, assume based on name?
                    # Better to rely on type if available.
                    if not raid_level:
                        raid_level = child.get("fstype") or "raid"  # fallback
                    return

                # Recurse
                if "children" in child:
                    find_raid_info(child["children"])

        find_raid_info(raw_partitions)

        for p in raw_partitions:
            p_path = p.get("path")
            lsblk_mountpoint = p.get("mountpoint")

            # Find all mounts for this partition from our findmnt map
            partition_mounts = []
            if p_path and p_path in mount_map:
                for m in mount_map[p_path]:
                    partition_mounts.append(
                        MountPoint(
                            path=m.get("target"),
                            options=m.get("options"),
                            fstype=m.get("fstype"),
                            source=m.get("source"),
                        )
                    )

            # Determine is_system based on ALL mounts
            # Check lsblk reported mountpoint
            if lsblk_mountpoint in ["/", "/boot", "/boot/efi", "/etc", "/var", "/usr"]:
                is_system = True

            # Check findmnt reported mounts
            for pm in partition_mounts:
                if pm.path in ["/", "/boot", "/boot/efi", "/etc", "/var", "/usr"]:
                    is_system = True

            # Also check for swap
            if p.get("fstype") == "swap":
                is_system = True

            partitions.append(
                Partition(
                    name=p.get("name"),
                    path=p_path,
                    size=int(p.get("size") or 0),
                    fstype=p.get("fstype"),
                    uuid=p.get("uuid"),
                    mountpoint=lsblk_mountpoint,  # Keep for compat, though it might be just one of many
                    mountpoints=partition_mounts,
                )
            )

        # If disk itself has a mountpoint (filesystem directly on disk)
        # Check lsblk
        if device.get("mountpoint"):
            if device.get("mountpoint") in ["/", "/boot", "/boot/efi"]:
                is_system = True

        # Check findmnt for the disk device itself
        if device.get("path") in mount_map:
            for m in mount_map[device.get("path")]:
                if m.get("target") in ["/", "/boot", "/boot/efi"]:
                    is_system = True

        # Determine availability:
        # Considered available if not system disk and has no partitions
        # OR has partitions but they are not mounted (though this is risky, so let's stick to empty for now)
        # Ideally, we'd check for partition table signatures, but lsblk children check is a good proxy.
        # For safety: Available only if NO children and NO fstype on the disk itself.
        available = not is_system and not raw_partitions and not device.get("fstype")

        disk = Disk(
            name=device.get("name"),
            path=device.get("path"),
            size=int(device.get("size") or 0),
            model=device.get("model"),
            serial=device.get("serial"),
            rotational=bool(device.get("rota")),
            partitions=partitions,
            is_system=is_system,
            available=available,
            raid_group=raid_group,
            raid_level=raid_level,
        )
        disks.append(disk)

    return disks


def get_unused_disks() -> List[Disk]:
    """Returns only disks marked as available."""
    return [d for d in get_system_disks() if d.available]
