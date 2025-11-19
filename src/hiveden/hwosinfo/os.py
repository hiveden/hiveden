import os
import platform


def get_os_info():
    """Return a dictionary with OS information."""
    info = {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'hostname': platform.node(),
    }

    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    info[key.lower()] = value.strip('"')

    return info
