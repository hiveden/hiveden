from typing import List
from hiveden.docker.models import DockerContainer, EnvVar, Port, Mount

def get_default_containers() -> List[DockerContainer]:
    return [
        DockerContainer(
            name="postgres",
            image="postgres:latest",
            env=[
                EnvVar(name="POSTGRES_PASSWORD", value="postgres"),
                EnvVar(name="POSTGRES_DB", value="hiveden")
            ],
            ports=[Port(host_port=5432, container_port=5432, protocol="tcp")],
            mounts=[
                Mount(
                    source="postgres",  # Relative to app directory
                    target="/var/lib/postgresql",
                    type="bind",
                    is_app_directory=True
                )
            ]
        ),
        DockerContainer(
            name="redis",
            image="redis:latest",
            ports=[Port(host_port=6379, container_port=6379, protocol="tcp")],
            mounts=[
                Mount(
                    source="redis",  # Relative to app directory
                    target="/data",
                    type="bind",
                    is_app_directory=True
                )
            ]
        ),
        DockerContainer(
            name="traefik",
            image="traefik:latest",
            command=[
                "--api.insecure=true",
                "--providers.docker=true",
                "--providers.docker.exposedbydefault=false",
                "--entrypoints.web.address=:80",
                "--entrypoints.websecure.address=:443"
            ],
            ports=[
                Port(host_port=80, container_port=80, protocol="tcp"),
                Port(host_port=443, container_port=443, protocol="tcp"),
                Port(host_port=8080, container_port=8080, protocol="tcp")
            ],
            mounts=[
                Mount(
                    source="/var/run/docker.sock",
                    target="/var/run/docker.sock",
                    type="bind",
                    is_app_directory=False
                )
            ]
        )
    ]
