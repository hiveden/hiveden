from typing import Any, Dict


def normalize_volume_attrs(attrs: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw Docker volume attrs into response-safe fields."""
    return {
        "name": attrs.get("Name", ""),
        "driver": attrs.get("Driver", ""),
        "mountpoint": attrs.get("Mountpoint", ""),
        "created_at": attrs.get("CreatedAt", ""),
        "labels": attrs.get("Labels"),
        "scope": attrs.get("Scope", ""),
        "options": attrs.get("Options"),
    }
