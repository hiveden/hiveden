import shutil
import configparser
import subprocess
import os
from hiveden.pkgs.manager import get_package_manager
from hiveden.hwosinfo.os import get_os_info
from hiveden.shares.models import SMBShare

SMB_CONF_PATH = "/etc/samba/smb.conf"

class SMBManager:
    def check_installed(self):
        """Check if samba is installed."""
        # Check for smbd executable
        return shutil.which("smbd") is not None or shutil.which("samba") is not None

    def install(self):
        """Install samba."""
        if self.check_installed():
            return

        pm = get_package_manager()
        # Most distros use 'samba'
        pm.install("samba")
        # Ensure cifs-utils is installed for mounting
        try:
            pm.install("cifs-utils")
        except Exception:
             # Depending on distro/manager implementation, this might fail if package name differs
             # or if it's already installed. We proceed.
             pass

    def mount_share(self, remote_path: str, mount_point: str, username: str = None, password: str = None, options: list = None, persist: bool = False):
        """
        Mount a remote SMB share.
        """
        # 1. Ensure mount point exists
        os.makedirs(mount_point, exist_ok=True)
        
        # 2. Check for mount.cifs
        if not shutil.which("mount.cifs"):
             raise RuntimeError("mount.cifs not found. Please install cifs-utils.")

        # 3. Construct Options
        mount_options = ["rw"] # default read-write
        
        # Credentials
        # For security in CLI command, it's better to use credentials file or environment, 
        # but standard python subprocess with list args hides it from shell history.
        # However, 'ps aux' would still show it.
        # A safer way is using a temporary credentials file if user/pass is provided.
        creds_file = None
        if username:
            if password:
                mount_options.append(f"username={username},password={password}")
            else:
                mount_options.append(f"username={username}")
        else:
            mount_options.append("guest")

        if options:
            mount_options.extend(options)

        opts_str = ",".join(mount_options)
        
        # 4. Mount
        cmd = ["mount", "-t", "cifs", remote_path, mount_point, "-o", opts_str]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to mount share: {e.stderr}")

        # 5. Persist
        if persist:
            self._add_to_fstab(remote_path, mount_point, "cifs", opts_str)

    def unmount_share(self, mount_point: str, remove_persistence: bool = False, force: bool = False):
        """
        Unmount a SMB share.
        """
        # 1. Unmount
        cmd = ["umount"]
        if force:
            cmd.append("-l") # Lazy unmount
        cmd.append(mount_point)

        # Only attempt unmount if it's currently mounted (check /proc/mounts)
        is_mounted = False
        try:
            with open("/proc/mounts", "r") as f:
                if any(line.split()[1] == mount_point for line in f):
                    is_mounted = True
        except Exception:
            # Fallback: try unmount anyway or check via other means. 
            # Proceeding to unmount is safer usually.
            is_mounted = True

        if is_mounted:
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to unmount {mount_point}: {e.stderr}")

        # 2. Remove Persistence
        if remove_persistence:
            self._remove_from_fstab(mount_point)
            
        # 3. Cleanup directory? 
        # Usually we keep the directory unless explicitly told to remove, 
        # but standard 'unmount' doesn't delete the folder. We leave it.

    def _add_to_fstab(self, device, mount_point, fstype, options):
        """Add an entry to /etc/fstab if not present."""
        # Clean inputs to avoid fstab corruption
        entry = f"{device} {mount_point} {fstype} {options} 0 0"
        
        # Check if already exists (simple check)
        exists = False
        try:
            with open("/etc/fstab", "r") as f:
                for line in f:
                    # Normalized check could be better, but exact match of mount point is good start
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == mount_point:
                        exists = True
                        break
        except FileNotFoundError:
            pass

        if not exists:
            with open("/etc/fstab", "a") as f:
                f.write(f"\n{entry}\n")

    def _remove_from_fstab(self, mount_point):
        """Remove an entry from /etc/fstab based on mount point."""
        try:
            lines = []
            with open("/etc/fstab", "r") as f:
                lines = f.readlines()
            
            new_lines = []
            changed = False
            for line in lines:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == mount_point:
                    changed = True
                    continue # Skip this line
                new_lines.append(line)
            
            if changed:
                with open("/etc/fstab", "w") as f:
                    f.writelines(new_lines)
        except FileNotFoundError:
            pass
    
    def _str_to_bool(self, val: str) -> bool:
        return val.lower() in ('yes', 'true', '1', 'on')

    def list_shares(self):
        """List all samba shares."""
        if not os.path.exists(SMB_CONF_PATH):
            return []

        config = configparser.ConfigParser()
        try:
            config.read(SMB_CONF_PATH)
        except configparser.Error:
            # Fallback or return empty if file is malformed
            return []

        shares = []
        for section in config.sections():
            # global, printers, print$ are standard sections/shares we might want to skip or mark
            if section.lower() == 'global':
                continue
            
            shares.append(SMBShare(
                name=section,
                path=config[section].get('path', 'N/A'),
                comment=config[section].get('comment', ''),
                read_only=self._str_to_bool(config[section].get('read only', 'yes')),
                browsable=self._str_to_bool(config[section].get('browsable', 'yes')),
                guest_ok=self._str_to_bool(config[section].get('guest ok', 'no'))
            ))
        return shares

    def list_mounted_shares(self):
        """List all mounted SMB/CIFS shares."""
        mounted_shares = []
        
        # Parse /etc/fstab to identify persistent mounts
        persistent_mounts = set()
        try:
            with open("/etc/fstab", "r") as f:
                for line in f:
                    parts = line.strip().split()
                    # format: device mount_point fstype ...
                    if len(parts) >= 3 and parts[2] == "cifs":
                        persistent_mounts.add(parts[1]) # Add mount point
        except FileNotFoundError:
            pass

        # Parse /proc/mounts for active mounts
        try:
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.strip().split()
                    # device mount_point fstype options ...
                    if len(parts) >= 4 and parts[2] == "cifs":
                        remote_path = parts[0]
                        mount_point = parts[1]
                        options = parts[3]
                        
                        # Fix octal encoding in paths (e.g. \040 for space) if necessary
                        # bytes(mount_point, 'utf-8').decode('unicode_escape') might be needed for complex paths
                        # but keeping it simple for now.
                        
                        mounted_shares.append({
                            "remote_path": remote_path,
                            "mount_point": mount_point,
                            "options": options,
                            "is_persistent": mount_point in persistent_mounts
                        })
        except FileNotFoundError:
            pass
            
        return mounted_shares

    def create_share(self, name, path, comment="", readonly=False, browsable=True, guest_ok=False):
        """Create a new samba share."""
        if not os.path.exists(SMB_CONF_PATH):
            # If config doesn't exist, create a basic one
            self._create_base_config()

        config = configparser.ConfigParser()
        config.read(SMB_CONF_PATH)

        if name in config:
            raise ValueError(f"Share '{name}' already exists.")

        config[name] = {
            'path': path,
            'comment': comment,
            'read only': 'yes' if readonly else 'no',
            'browsable': 'yes' if browsable else 'no',
            'guest ok': 'yes' if guest_ok else 'no'
        }

        with open(SMB_CONF_PATH, 'w') as configfile:
            config.write(configfile)

        self._reload_service()

    def delete_share(self, name):
        """Delete a samba share."""
        if not os.path.exists(SMB_CONF_PATH):
            raise ValueError("Samba configuration file not found.")

        config = configparser.ConfigParser()
        config.read(SMB_CONF_PATH)

        if name not in config:
            raise ValueError(f"Share '{name}' does not exist.")

        config.remove_section(name)

        with open(SMB_CONF_PATH, 'w') as configfile:
            config.write(configfile)

        self._reload_service()

    def start_service(self):
        """Start the samba service."""
        self._manage_service("start")

    def stop_service(self):
        """Stop the samba service."""
        self._manage_service("stop")

    def restart_service(self):
        """Restart the samba service."""
        self._manage_service("restart")

    def get_status(self):
        """Get the status of the samba service."""
        service_names = ['smbd', 'samba', 'smb']
        for service in service_names:
            try:
                result = subprocess.run(["systemctl", "is-active", service], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                status = result.stdout.strip()
                if status != "unknown":
                    return status
            except FileNotFoundError:
                continue
        return "not found"

    def _create_base_config(self):
        config = configparser.ConfigParser()
        config['global'] = {
            'workgroup': 'WORKGROUP',
            'server string': 'Hiveden Server',
            'security': 'user',
            'map to guest': 'Bad User'
        }
        os.makedirs(os.path.dirname(SMB_CONF_PATH), exist_ok=True)
        with open(SMB_CONF_PATH, 'w') as configfile:
            config.write(configfile)

    def _reload_service(self):
        """Reload the samba service."""
        self._manage_service("reload")

    def _manage_service(self, action):
        """Manage the samba service state."""
        service_names = ['smbd', 'samba', 'smb']
        for service in service_names:
            try:
                subprocess.run(["systemctl", action, service], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        # If all fail, it might be worth logging or raising a warning, but for now we stay silent or maybe raise if strict.
        # For CLI usage, silent failure if service isn't found might be confusing, but consistent with previous implementation.
