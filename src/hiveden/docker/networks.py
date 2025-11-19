import docker

client = docker.from_env()


def create_network(name, **kwargs):
    """Create a new Docker network."""
    return client.networks.create(name, **kwargs)


def get_network(network_id):
    """Get a Docker network by its ID."""
    return client.networks.get(network_id)


def list_networks(**kwargs):
    """List all Docker networks."""
    return client.networks.list(**kwargs)


def remove_network(network_id):
    """Remove a Docker network."""
    network = get_network(network_id)
    network.remove()
    return network
