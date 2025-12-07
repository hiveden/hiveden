from typing import List, Optional
from hiveden.storage.devices import get_system_disks, get_unused_disks
from hiveden.storage.strategies import generate_strategies
from hiveden.storage.models import Disk, StorageStrategy, DiskDetail, SmartData
from hiveden.jobs.manager import JobManager
from hiveden.hwosinfo.hw import get_smart_info

class StorageManager:
    def list_disks(self) -> List[Disk]:
        return get_system_disks()

    def get_disk_details(self, device_name: str) -> Optional[DiskDetail]:
        """
        Retrieves detailed information for a specific disk, including SMART data.
        """
        all_disks = get_system_disks()
        target_disk = next((d for d in all_disks if d.name == device_name), None)
        
        if not target_disk:
            return None

        # Get SMART info
        # Usually smartctl needs full path, e.g. /dev/sda
        # Our disk.path should have it.
        smart_raw = get_smart_info(target_disk.path)
        
        smart_data = None
        vendor = None
        firmware = None
        bus = None # smartctl often tells protocol

        if smart_raw:
            # Parse SmartData from raw JSON
            # Structure depends on smartctl version and device type
            # Basic parsing attempt:
            smart_status = smart_raw.get("smart_status", {})
            passed = smart_status.get("passed", False)
            
            # Temperature
            temp = smart_raw.get("temperature", {}).get("current")
            
            # Power on hours
            poh = smart_raw.get("power_on_time", {}).get("hours")
            
            # Power cycles
            cycles = smart_raw.get("power_cycle_count")

            # Model/Serial/Firmware often in 'model_name', 'serial_number', 'firmware_version' keys
            # or inside 'device' key
            device_info = smart_raw.get("device", {})
            model = smart_raw.get("model_name") or device_info.get("model_name")
            serial = smart_raw.get("serial_number") or device_info.get("serial_number")
            firmware = smart_raw.get("firmware_version") or device_info.get("firmware_version")
            
            # Rotation rate
            rotation = smart_raw.get("rotation_rate")
            
            # Attributes table
            ata_smart = smart_raw.get("ata_smart_attributes", {})
            attributes = ata_smart.get("table", [])

            smart_data = SmartData(
                healthy=passed,
                health_status="Passed" if passed else "Failed",
                temperature=temp,
                power_on_hours=poh,
                power_cycles=cycles,
                model_name=model,
                serial_number=serial,
                firmware_version=firmware,
                rotation_rate=rotation,
                attributes=attributes
            )
            
            # Vendor/Bus often in device info
            # protocol: "ATA", "SCSI", "NVMe"
            bus = device_info.get("protocol")

        return DiskDetail(
            **target_disk.dict(),
            vendor=vendor, # Might be extracted from model or lsblk
            bus=bus,
            smart=smart_data
        )

    def get_strategies(self) -> List[StorageStrategy]:
        unused = get_unused_disks()
        return generate_strategies(unused)

    def apply_strategy(self, strategy: StorageStrategy) -> str:
        """
        Applies the given storage strategy.
        Returns the Job ID of the background task.
        """
        commands = []
        mount_point = "/mnt/hiveden-storage"
        
        commands.append(f"echo 'Starting configuration for {strategy.name}...'")
        
        # 1. Cleanup and Prepare Disks
        disks_str = " ".join(strategy.disks)
        
        # Unmount any existing mounts on these disks (best effort) and wipe
        for disk in strategy.disks:
            commands.append(f"echo 'Preparing {disk}...'")
            # lazy unmount to avoid busy errors, || true to ignore if not mounted
            commands.append(f"umount -l {disk}* 2>/dev/null || true")
            commands.append(f"wipefs -a {disk}")
        
        mount_dev = ""

        if strategy.raid_level == "single":
            # Btrfs single mode (JBOD)
            commands.append(f"echo 'Formatting disks in Single mode...'")
            # -f: force, -d single: data single, -m single: metadata single
            commands.append(f"mkfs.btrfs -f -d single -m single {disks_str}")
            mount_dev = strategy.disks[0] # Mount any device in the pool
            
        elif strategy.raid_level.startswith("raid"):
            level = strategy.raid_level.replace("raid", "")
            md_dev = "/dev/md0"
            mount_dev = md_dev
            
            commands.append(f"echo 'Configuring RAID {level}...'")
            
            # Stop existing array if it exists
            commands.append(f"mdadm --stop {md_dev} 2>/dev/null || true")
            
            # Zero superblocks on all disks to remove old raid info
            commands.append(f"mdadm --zero-superblock {disks_str} 2>/dev/null || true")
            
            # Create Array
            commands.append(f"mdadm --create {md_dev} --level={level} --raid-devices={len(strategy.disks)} {disks_str} --run --force")
            
            # Format
            commands.append(f"echo 'Formatting RAID array...'")
            commands.append(f"mkfs.btrfs -f {md_dev}")

        # Mounting
        commands.append(f"echo 'Mounting storage to {mount_point}...'")
        commands.append(f"mkdir -p {mount_point}")
        commands.append(f"mount {mount_dev} {mount_point}")
        
        commands.append("echo 'Storage configuration completed successfully.'")
        
        # Join commands into a single shell command
        full_command = " && ".join(commands)
        
        # Submit to JobManager
        job_manager = JobManager()
        return job_manager.create_job(full_command)
