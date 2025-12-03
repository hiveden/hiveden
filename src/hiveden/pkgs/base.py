from abc import ABC, abstractmethod
import subprocess
from typing import List

from hiveden.pkgs.models import RequiredPackage


class PackageManager(ABC):
    @abstractmethod
    def list_installed(self):
        pass

    @abstractmethod
    def install(self, package):
        pass

    @abstractmethod
    def remove(self, package):
        pass

    @abstractmethod
    def search(self, package):
        pass

    @abstractmethod
    def get_install_command(self, package: str) -> str:
        pass

    @abstractmethod
    def get_check_installed_command(self, package: str) -> str:
        pass

    def is_installed(self, package: str) -> bool:
        command = self.get_check_installed_command(package)
        try:
            subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    @abstractmethod
    def get_required_packages(self) -> List[RequiredPackage]:
        pass


