import docker

from .. import settings

client = docker.Client(base_url=settings.DOCKER_SOCKET)


def find_container(name):
    # prepen / to name
    name = '/{}'.format(name)
    containers = client.containers(all=True)
    containers = [c for c in containers if name in c['Names']]
    if not containers:
        return None
    return containers[0]


def list_containers(all=True):
    client = docker.Client()
    return client.containers(all=all)
