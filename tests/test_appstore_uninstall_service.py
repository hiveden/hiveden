import asyncio
from types import SimpleNamespace

from hiveden.appstore.uninstall_service import AppUninstallService


class _FakeCatalog:
    def __init__(self, resources):
        self._resources = resources
        self.deleted = False
        self.status_calls = []

    def get_app(self, app_id):
        return SimpleNamespace(
            app_id=app_id,
            version="1.0.0",
            install_status="installed",
            installed=True,
        )

    def list_resources(self, app_id):
        return self._resources

    def delete_resources(self, app_id):
        self.deleted = True

    def set_installation_status(
        self,
        app_id,
        status,
        installed_version=None,
        last_error=None,
    ):
        self.status_calls.append(
            {
                "app_id": app_id,
                "status": status,
                "installed_version": installed_version,
                "last_error": last_error,
            }
        )


class _FakeJobManager:
    def __init__(self):
        self.logs = []

    async def log(self, _job_id, message):
        self.logs.append(message)


def test_uninstall_skips_external_containers_and_only_unlinks():
    resources = [
        {
            "resource_type": "container",
            "resource_name": "pihole",
            "metadata": {"external": True},
        }
    ]
    service = AppUninstallService.__new__(AppUninstallService)
    service.catalog = _FakeCatalog(resources)
    service.docker = SimpleNamespace(_resolve_app_directory=lambda: "/tmp")

    removed = []
    service._remove_container = lambda *args, **kwargs: removed.append((args, kwargs))
    manager = _FakeJobManager()

    asyncio.run(
        service.uninstall_app(
            job_id="job-1",
            job_manager=manager,
            app_id="pi-hole",
            delete_data=False,
            delete_databases=False,
            delete_dns=False,
        )
    )

    assert removed == []
    assert any("Skipping external container pihole" in item for item in manager.logs)
    assert service.catalog.deleted is True
    assert service.catalog.status_calls[-1]["status"] == "not_installed"
