from abc import ABCMeta, abstractmethod
import time
import os
import shutil
import socket
import logging

from .. import settings
from ..utils.container import find_container

logger = logging.getLogger(__name__)


class DBTimeoutException(Exception):
    pass


class AbstractDatabase(metaclass=ABCMeta):
    """Abstract implementation for a database backend"""

    def __init__(self, docker_client, template, name=None):
        self.client = docker_client
        if name:
            self.name = '{prefix}{template}-{name}'.format(
                prefix=settings.CONTAINER_PREFIX, template=template, name=name)
        else:
            self.name = '{prefix}{template}'.format(
                prefix=settings.CONTAINER_PREFIX, template=template)

        self.container = find_container(self.name)
        if not self.container:
            labels = {
                'com.myaas.provider': self.provider,
                'com.myass.is_template': 'True' if name is None else 'False',
                'com.myass.template': template,
                'com.myass.instance': name,
                'com.myass.name': self.name
            }
            self.create(labels)

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
    @abstractmethod
    def provider(self):
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

    def create(self, labels={}):
        self.container = self.client.create_container(
            image=self.image,
            name=self.name,
            environment=self.environment,
            ports=[self.internal_port],
            volumes=[self.datadir_database],
            host_config=self._get_host_config_definition(),
            labels=labels)

    @abstractmethod
    def test_connection(self, timeout=1):
        if not self.internal_port:
            raise Exception("Could not find port for connection")
        if not self.internal_ip:
            raise Exception("Could not find host for connection")

    def start(self):
        self.client.start(self.container)

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
        while tries < 30:
            if self.test_connection():
                return
            time.sleep(5)
            tries += 1

        raise DBTimeoutException("Could not connect with database, max retries reached")

    def inspect(self):
        data = self.client.inspect_container(self.container)
        if not data:
            raise Exception("Docker inspect data not available")
        return data

    def _get_volumes_definition(self):
        return [self.datadir_database]

    def _get_host_config_definition(self):
        "create host_config object with permanent port mapping"
        host_config = self.client.create_host_config(
            port_bindings={
                self.internal_port: self._get_free_port(),
            },
            binds={
                self.datadir_host: {'bind': self.datadir_database, 'ro': False}
            },
            mem_limit=self.mem_limit,
            restart_policy=self.restart_policy
        )
        logger.debug(host_config)

        return host_config

    def _get_port_bindings(self):
        return {self.internal_port: ('0.0.0.0',)}

    def _datadir_created(self):
        return os.path.isdir(self.datadir_launcher)

    def _delete_volume_data(self):
        shutil.rmtree(self.datadir_launcher)

    def _get_free_port(self):
        """
        This method finds a free port number for new containers to be created,
        it releases the port just before returning the port number, so there is
        a chance for another process to get it, let's see if it works.

        This requires the mariadb-replicator container to be running with
        --net=host otherwise the port returned by this method will be a free port
        inside the container, but may not be free on the host machine.
        """
        s = socket.socket()
        s.bind(("", 0))
        (ip, port) = s.getsockname()
        s.close()
        logger.debug("Assigning port {}".format(port))
        return port
