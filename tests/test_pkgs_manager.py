import pytest
from unittest.mock import Mock, patch
from hiveden.pkgs.manager import get_system_required_packages
from hiveden.pkgs.models import RequiredPackage, PackageStatus, PackageOperation, OSType
from hiveden.pkgs.base import PackageManager

class MockPackageManager(PackageManager):
    def list_installed(self):
        return []
    def install(self, package):
        pass
    def remove(self, package):
        pass
    def search(self, package):
        return []
    def get_install_command(self, package):
        return f"install {package}"
    def get_check_installed_command(self, package):
        return f"check {package}"
    def is_installed(self, package):
        return package == "installed-pkg"

# Mock OS info to simulate an Ubuntu system
MOCK_OS_INFO = {'id': 'ubuntu'}

@patch('hiveden.pkgs.manager.get_package_manager')
@patch('hiveden.pkgs.manager.get_os_info')
@patch('hiveden.pkgs.manager.get_all_required_packages')
def test_get_system_required_packages(mock_get_registry, mock_get_os, mock_get_pm):
    mock_pm = MockPackageManager()
    mock_get_pm.return_value = mock_pm
    mock_get_os.return_value = MOCK_OS_INFO
    
    # Setup registry with mixed OS and tags
    mock_get_registry.return_value = [
        RequiredPackage(
            name="installed-pkg", title="A", description="D", 
            operation=PackageOperation.INSTALL, 
            os_types=[OSType.ALL], tags=["storage"]
        ),
        RequiredPackage(
            name="missing-pkg", title="B", description="D", 
            operation=PackageOperation.UNINSTALL, 
            os_types=[OSType.UBUNTU], tags=["system"]
        ),
        RequiredPackage(
            name="wrong-os-pkg", title="C", description="D", 
            operation=PackageOperation.INSTALL, 
            os_types=[OSType.FEDORA], tags=["storage"]
        )
    ]
    
    # Test 1: No tags (Default) -> Should get Ubuntu + ALL packages
    packages = get_system_required_packages()
    assert len(packages) == 2
    assert packages[0].name == "installed-pkg"
    assert packages[1].name == "missing-pkg"
    
    # Test 2: Filter by tag "storage" -> Should get only installed-pkg
    packages_storage = get_system_required_packages(tags="storage")
    assert len(packages_storage) == 1
    assert packages_storage[0].name == "installed-pkg"
    
    # Test 3: Filter by tag "system" -> Should get only missing-pkg
    packages_system = get_system_required_packages(tags="system")
    assert len(packages_system) == 1
    assert packages_system[0].name == "missing-pkg"
