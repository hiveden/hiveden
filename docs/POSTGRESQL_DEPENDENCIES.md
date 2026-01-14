# Multi-Distribution PostgreSQL Dependency Strategy

## Overview

This document explains how Hiveden handles PostgreSQL dependencies across Ubuntu, Fedora, and Arch Linux.

## Strategy: System-Native PostgreSQL Libraries

We use **`psycopg2`** (not `psycopg2-binary`) and let each distribution's package manager install the system-level PostgreSQL client libraries.

### Why This Approach?

1. **Production-ready**: Uses system-optimized PostgreSQL libraries
2. **Distribution-native**: Leverages each distro's package manager for dependency resolution
3. **Maintainable**: Single Python dependency definition, system dependencies handled per-distro
4. **Secure**: Automatic security updates through system package manager
5. **Smaller package size**: Doesn't bundle PostgreSQL libraries in the Python wheel

## Implementation

### Python Dependencies (pyproject.toml & requirements.txt)

```toml
dependencies = [
    "psycopg2",  # NOT psycopg2-binary
    # ... other deps
]
```

### System Package Dependencies

Each distribution package declares the PostgreSQL client library:

#### Ubuntu/Debian (`packaging/debian/control`)

```
Depends: python3-psycopg2, ...
```

- Package name: `python3-psycopg2`
- Installed via: `apt install python3-psycopg2`

#### Fedora/RHEL (`packaging/fedora/hiveden.spec`)

```
Requires: python3-psycopg2
```

- Package name: `python3-psycopg2`
- Installed via: `dnf install python3-psycopg2`

#### Arch Linux (`packaging/arch/PKGBUILD`)

```
depends=('python-psycopg2')
```

- Package name: `python-psycopg2`
- Installed via: `pacman -S python-psycopg2`

## For Development Environments

If developers are using pip/uv directly (not system packages), they have two options:

### Option 1: Install system PostgreSQL development libraries first

```bash
# Ubuntu/Debian
sudo apt install libpq-dev python3-dev

# Fedora/RHEL
sudo dnf install postgresql-devel python3-devel

# Arch Linux
sudo pacman -S postgresql-libs

# Then install Python packages
pip install -e .
```

### Option 2: Use psycopg2-binary for development only

Create a `requirements-dev.txt`:

```
-e .
psycopg2-binary  # Override psycopg2 for development convenience
```

This allows developers to work without system PostgreSQL libraries, while production packages use system libraries.

## Troubleshooting

### Error: "DistributionNotFound: The 'psycopg2-binary' distribution was not found"

**Cause**: Package declares `psycopg2-binary` but system has `psycopg2` installed

**Solution**: Change Python dependencies from `psycopg2-binary` to `psycopg2` (already done)

### Error: "psycopg2-binary" when building packages

**Cause**: Old cache or build artifacts referencing old dependency

**Solution**:

```bash
# Clean build artifacts
rm -rf build/ dist/ *.egg-info/

# Rebuild package
python -m build
```

### Import Error: No module named 'psycopg2'

**Cause**: PostgreSQL client library not installed

**Solution**: Install the appropriate system package:

- Ubuntu: `sudo apt install python3-psycopg2`
- Fedora: `sudo dnf install python3-psycopg2`
- Arch: `sudo pacman -S python-psycopg2`

## Summary

✅ **Python packages**: Use `psycopg2` (not `-binary`)  
✅ **Debian packages**: Declare `python3-psycopg2` dependency  
✅ **Fedora packages**: Declare `python3-psycopg2` dependency  
✅ **Arch packages**: Declare `python-psycopg2` dependency  
✅ **Development**: Use system libs OR psycopg2-binary in requirements-dev.txt

## CI/CD Builds

When building packages in CI/CD (GitHub Actions, GitLab CI, etc.), you need to pre-install dependencies before running the build tools:

### Arch Linux (makepkg)

```bash
# Pre-install dependencies before running makepkg
pacman -Syu --noconfirm python-psycopg2
# Then run makepkg
makepkg -sf
```

**Why?** The `-s` flag in `makepkg` tries to install dependencies interactively, which fails in non-interactive CI environments. Pre-installing dependencies solves this.

### Debian (debuild)

Dependencies are automatically installed during the build process via the `Depends:` field in the control file. No special action needed.

### Fedora (rpmbuild)

Dependencies are typically installed during `rpmbuild -ba`. If issues occur, pre-install:

```bash
dnf install -y python3-psycopg2
rpmbuild -ba hiveden.spec
```
