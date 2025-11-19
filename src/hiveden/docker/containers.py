import docker

client = docker.from_env()


def create_container(image, command=None, **kwargs):
    """Create a new Docker container."""
    return client.containers.create(image, command, **kwargs)


def get_container(container_id):
    """Get a Docker container by its ID."""
    return client.containers.get(container_id)


def list_containers(all=False, **kwargs):
    """List all Docker containers."""
    return client.containers.list(all=all, **kwargs)


def stop_container(container_id):
    """Stop a running Docker container."""
    container = get_container(container_id)
    container.stop()
    return container


def remove_container(container_id):
    """Remove a Docker container."""
    container = get_container(container_id)
    container.remove()
    return container
