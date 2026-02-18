from types import SimpleNamespace

from hiveden.appstore.adoption_service import AppAdoptionService


class _FakeCatalog:
    def __init__(self):
        self.resources = []
        self.status_calls = []

    def get_app(self, app_id):
        return SimpleNamespace(
            app_id=app_id,
            version="1.0.0",
            compose_url="https://example.com/docker-compose.yml",
            install_status="not_installed",
        )

    def list_container_resource_owners(self, container_name, exclude_app_id=None):
        return []

    def delete_resources_by_type(self, app_id, resource_type):
        return None

    def delete_resource(self, app_id, resource_type, resource_name):
        return None

    def add_resource(self, app_id, resource_type, resource_name, metadata=None):
        self.resources.append(
            {
                "app_id": app_id,
                "resource_type": resource_type,
                "resource_name": resource_name,
                "metadata": metadata or {},
            }
        )

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


class _FakeDocker:
    def get_container(self, _identifier):
        return SimpleNamespace(
            Id="abc123",
            Name="pihole",
            Image="pihole/pihole:latest",
            Status="running",
        )


def test_adopt_app_links_external_container_and_marks_installed():
    service = AppAdoptionService.__new__(AppAdoptionService)
    service.catalog = _FakeCatalog()
    service.docker = _FakeDocker()
    service._get_expected_images = lambda _compose_url, _warnings: {"pihole/pihole"}

    result = service.adopt_app(
        app_id="pi-hole",
        container_names_or_ids=["pihole"],
    )

    assert len(result.containers) == 1
    assert service.catalog.resources[0]["resource_type"] == "container"
    assert service.catalog.resources[0]["metadata"]["external"] is True
    assert service.catalog.status_calls[-1]["status"] == "installed"


def test_adopt_app_rejects_image_mismatch_without_force():
    service = AppAdoptionService.__new__(AppAdoptionService)
    service.catalog = _FakeCatalog()
    service.docker = _FakeDocker()
    service._get_expected_images = lambda _compose_url, _warnings: {"nginx"}

    try:
        service.adopt_app(
            app_id="pi-hole",
            container_names_or_ids=["pihole"],
            force=False,
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "does not match expected images" in str(exc)
