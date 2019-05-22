import docker
from os import getenv
from multiprocessing import cpu_count
from random import sample as random_sample
from collections import Counter

from .. import settings

client = docker.Client(base_url=settings.DOCKER_HOST)


def find_container(name):
    # prepend / to name
    name = f'/{name}'
    containers = client.containers(all=True)
    containers = [c for c in containers if name in c['Names']]
    if not containers:
        return None
    return containers[0]


def list_containers(all=True):
    client = docker.Client()
    return client.containers(all=all)


def translate_host_basedir(path):
    # TODO: if container is created with a custom hostname this will not work
    # improve self id detection in the future.
    self_id = getenv('HOSTNAME')
    self_container = client.containers(filters={'id': self_id})[0]
    mount_config = client.inspect_container(self_container)['Mounts']
    for mount in mount_config:
        if mount['Destination'] == settings.BASE_DIR:
            break

    if mount['Destination'] != settings.BASE_DIR:
        raise KeyError("Could not find %s mountpoint" % settings.BASE_DIR)

    return path.replace(mount['Destination'], mount['Source'], 1)


def get_random_cpuset(cores_to_assign):
    available_cores = cpu_count()
    random_cores = random_sample(range(available_cores), cores_to_assign)
    return ",".join(map(str, random_cores))

def get_mapped_cpuset():
    # fake a static variable
    if 'cnt' not in get_mapped_cpuset.__dict__:
        cpu_map = settings.CPU_MAP.split(':')
        get_mapped_cpuset.cnt = Counter(cpu_map)

    least_used = get_mapped_cpuset.cnt.most_common()[-1][0]
    get_mapped_cpuset.cnt[least_used] += 1

    return least_used
