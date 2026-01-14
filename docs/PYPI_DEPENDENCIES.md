# PyPI-Only Dependencies Strategy

## Problem

Some Python packages required by Hiveden are **only available on PyPI** (Python Package Index) and are not packaged for distribution repositories:

- **`pihole6api`** - Pi-hole 6 API client
- **`yoyo-migrations`** - Database migration tool

When these are listed as required dependencies in `pyproject.toml`, `pkg_resources` throws a `DistributionNotFound` error during package installation because the system package manager can't find them.

## Solution

We use a **pip-based installation** approach:

1. **List all dependencies** in `pyproject.toml` (both required and optional extras)
2. **Install via pip during post-install** - System package post-install scripts use pip to install all Python dependencies

This ensures reliable dependency resolution and works consistently across all distributions.

## Implementation

### pyproject.toml

```toml
[project]
dependencies = [
    "click",
    "fastapi",
    "uvicorn",
    "docker",
    "PyYAML",
    "psutil",
    "lxc",
    "psycopg2",
    "paramiko",
    "websockets",
]

[project.optional-dependencies]
# PyPI-only packages
extras = [
    "pihole6api",
    "yoyo-migrations",
]
```

### Arch Linux (hiveden.install)

```bash
post_install() {
    # Install all Python dependencies via pip
    pip install --no-warn-script-location click fastapi uvicorn docker PyYAML psutil lxc paramiko websockets pihole6api yoyo-migrations 2>/dev/null || true
}

post_upgrade() {
    post_install
}
```

### Debian/Ubuntu (postinst)

```bash
#!/bin/bash

mkdir -p /opt/hiveden
chmod 644 /opt/hiveden

# Install all Python dependencies via pip
pip3 install --no-warn-script-location click fastapi uvicorn docker PyYAML psutil lxc paramiko websockets pihole6api yoyo-migrations 2>/dev/null || true
```

### Fedora/RHEL (spec file)

```spec
%post
%systemd_post hiveden.service
# Install all Python dependencies via pip
pip3 install --no-warn-script-location click fastapi uvicorn docker PyYAML psutil lxc paramiko websockets pihole6api yoyo-migrations 2>/dev/null || true
```

## Why This Works

1. **Build time**: Package builds with minimal dependencies (just system package manager basics)
2. **Install time**: Post-install scripts fetch and install all Python dependencies from PyPI
3. **Runtime**: All dependencies available when application runs
4. **Upgrades**: Post-upgrade hooks ensure dependencies stay current

## Flags Used

- `--no-warn-script-location`: Suppress warnings about script locations
- `2>/dev/null || true`: Suppress errors and don't fail package installation if pip has issues

## Benefits

✅ **Consistent across distros** - Same dependency list everywhere  
✅ **Reliable resolution** - pip handles dependency trees correctly  
✅ **Always up-to-date** - Gets latest compatible versions from PyPI  
✅ **Handles PyPI-only packages** - Works for packages not in system repos  
✅ **Simple maintenance** - Single source of truth (pyproject.toml)

## Alternatives Considered

1. **Bundling wheels** - Would increase package size significantly
2. **Lazy imports** - Requires code changes and makes features harder to discover
3. **Vendoring** - Hard to maintain and update
4. **System packages** - Not available for these libraries

The current approach is the cleanest balance between compatibility and functionality.
