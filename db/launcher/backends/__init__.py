from abc import ABCMeta, abstractmethod
import time
import os
import shutil

from .. import settings
from ..utils.container import find_container


class DBTimeoutException(Exception):
    pass


class AbstractDatabase(metaclass=ABCMeta):
    """Abstract implementation for a database backend"""

    def __init__(self, docker_client, name):
        self.client = docker_client
        self.name = '{prefix}{name}'.format(
            prefix=settings.CONTAINER_PREFIX, name=name)
        self.container = find_container(self.name)
        if not self.container:
            self.create()

    @property
    @abstractmethod
    def datadir_database(self):
        pass

    @property
    def datadir_launcher(self):
        return os.path.join(settings.DATA_DIR, self.name)

    @property
    def datadir_host(self):
        return os.path.join(settings.HOST_DATA_DIR, self.name)

    @property
    @abstractmethod
    def image(self):
        pass

    @property
    @abstractmethod
    def environment(self):
        pass

    @property
    def mem_limit(self):
        return '1g'

    @property
    def internal_ip(self):
        return self.inspect()['NetworkSettings']['IPAddress']

    @property
    def external_ip(self):
        return settings.HOSTNAME

    @property
    def restart_policy(self):
        return {"MaximumRetryCount": 0, "Name": "always"}

    @property
    @abstractmethod
    def internal_port(self):
        pass

    @property
    def external_port(self):
        port_name = '{}/tcp'.format(self.internal_port)
        ports = self.inspect()['NetworkSettings']['Ports']
        if not ports:
            return None
        elif port_name not in ports:
            return None
        return ports[port_name][0]["HostPort"]

    @property
    def user(self):
        return "root"

    @property
    @abstractmethod
    def password(self):
        pass

    @property
    def database(self):
        return "default"

    def create(self):
        self.container = self.client.create_container(
            image=self.image,
            name=self.name,
            environment=self.environment,
            mem_limit=self.mem_limit,
            ports=[self.internal_port],
            volumes=self._get_volumes_definition())

    @abstractmethod
    def test_connection(self, timeout=1):
        if not self.internal_port:
            raise Exception("Could not find port for connection")
        if not self.internal_ip:
            raise Exception("Could not find host for connection")

    def start(self):
        self.client.start(self.container,
                          binds=self._get_volumes_bindings(),
                          port_bindings=self._get_port_bindings(),
                          restart_policy=self.restart_policy)

    def stop(self):
        self.client.stop(self.container)

    def running(self):
        return self.inspect()['State']['Running']

    def destroy(self):
        if self.running():
            self.stop()
        self.client.remove_container(self.container)
        self.container = None

    def purge(self):
        if self.container:
            self.destroy()

        if self._datadir_created():
            self._delete_volume_data()

    def wait_until_active(self):
        tries = 0
        while tries < 20:
            if self.test_connection():
                return
            time.sleep(3)
            tries += 1

        raise DBTimeoutException("Could not connect with database, max retries reached")

    def inspect(self):
        data = self.client.inspect_container(self.container)
        if not data:
            raise Exception("Docker inspect data not available")
        return data

    def _get_volumes_definition(self):
        return [self.datadir_database]

    def _get_volumes_bindings(self):
        return {
            self.datadir_host: {'bind': self.datadir_database, 'ro': False}
        }

    def _get_port_bindings(self):
        return {self.internal_port: ('0.0.0.0',)}

    def _datadir_created(self):
        return os.path.isdir(self.datadir_launcher)

    def _delete_volume_data(self):
        shutil.rmtree(self.datadir_launcher)
