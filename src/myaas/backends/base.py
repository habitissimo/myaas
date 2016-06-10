import logging

from abc import ABCMeta, abstractmethod, abstractproperty
from os.path import isdir, join as join_path
from time import sleep

from .. import settings
from ..utils.container import find_container, translate_host_basedir, get_random_cpuset
from ..utils.socket import reserve_port, test_tcp_connection
from ..utils.filesystem import copy_tree, rm_tree, rename

from .exceptions import (NonExistentDatabase, NonExistentTemplate,
                         NotReachableException, DBTimeoutException,
                         ImportInProgress, ContainerRunning)


logger = logging.getLogger(__name__)


class ContainerService():
    """
    Convinience wrappers arround docker client API
    """
    def __init__(self, client, container_name):
        self.client = client  # Docker client instance
        self.container = find_container(container_name)
        self.container_name = container_name

    @property
    def ports(self):
        return []

    @property
    def volumes(self):
        return []

    @property
    def environment(self):
        return {}

    @property
    def labels(self):
        return {}

    @property
    def cpuset(self):
        if not settings.CPU_PINNING:
            return None
        return get_random_cpuset()

    @property
    def memory_limit(self):
        return None

    @property
    def restart_policy(self):
        return None

    def start(self):
        self.client.start(self.container)

    def stop(self):
        self.client.stop(self.container)
        self.client.wait(self.container)

    def kill(self):
        self.client.kill(self.container)

    def running(self):
        return self.inspect()['State']['Running']

    def remove(self):
        if self.running():
            self.kill()

        self.client.remove_container(self.container)
        self.container = None

    def inspect(self):
        return self.client.inspect_container(self.container)

    def make_host_config(self):
        return {
            "port_bindings": {port: reserve_port() for port in self.ports},
            "mem_limit": self.memory_limit,
            "restart_policy": self.restart_policy,
        }

    def create_container(self, image):
        host_config = self.make_host_config()
        # remove empty properties from config dict
        host_config = {k: v for k, v in host_config.items() if v}

        return self.client.create_container(
            image=image,
            name=self.container_name,
            ports=self.ports,
            volumes=self.volumes,
            environment=self.environment,
            labels=self.labels,
            cpuset=self.cpuset,
            host_config=self.client.create_host_config(**host_config))


class PersistentContainerService(ContainerService):
    @property
    def datadir(self):
        return "/tmp"

    @property
    def backupdir(self):
        return join_path(settings.DATA_DIR, 'backup-' + self.container_name)

    @property
    def host_datadir(self):
        return join_path(settings.DATA_DIR, self.container_name)

    @property
    def volumes(self):
        return [self.datadir]

    def remove(self):
        super().remove()
        if isdir(self.host_datadir):
            rm_tree(self.host_datadir)

    def make_bindings_config(self):
        # host_datadir needs to be translated as the docker daemon runs on the
        # host and does not see the host directories trough a binded volume
        host_datadir = translate_host_basedir(self.host_datadir)
        return {host_datadir: {'bind': self.datadir, 'ro': False}}

    def make_host_config(self):
        config = super().make_host_config()
        config['binds'] = self.make_bindings_config()
        return config

    def do_backup(self, use_rename=False):
        if self.running():
            raise ContainerRunning()

        # remove previous backup if exists
        self.remove_backup()

        if not isdir(self.host_datadir):
            return  # nothing to backup

        if use_rename:
            rename(self.host_datadir, self.backupdir)
        else:
            copy_tree(self.host_datadir, self.backupdir)

    def remove_backup(self):
        if isdir(self.backupdir):
            rm_tree(self.backupdir)

    def restore_backup(self):
        if self.running():
            raise ContainerRunning()

        if not isdir(self.backupdir):
            return False

        rm_tree(self.host_datadir)
        rename(self.backupdir, self.host_datadir)

        return True


class AbstractDatabase(PersistentContainerService, metaclass=ABCMeta):
    """Abstract implementation for a database backend"""

    not_found_exception_class = NonExistentDatabase

    def __init__(self, client, template, name, create=False):
        container_name = self._make_container_name(template, name)

        super().__init__(client, container_name)

        self.template = template
        self.name = name
        self.create = create
        if not self.container:
            if not self.create:
                raise self.not_found_exception_class()
            self.container = self.create_container(self.image)

    @abstractproperty
    def datadir(self):
        pass

    @abstractproperty
    def image(self):
        pass

    @abstractproperty
    def provider_name(self):
        pass

    @abstractproperty
    def service_port(self):
        pass

    @property
    def internal_ip(self):
        return self.inspect()['NetworkSettings']['IPAddress']

    @property
    def restart_policy(self):
        return {"MaximumRetryCount": 0, "Name": "always"}

    @property
    def ports(self):
        return [self.service_port]

    @property
    def labels(self):
        return {
            'com.myaas.provider': self.provider_name,
            'com.myaas.is_template': 'False',
            'com.myaas.template': self.template,
            'com.myaas.instance': self.name,
        }

    @property
    def host_port(self):
        port_name = '{}/tcp'.format(self.service_port)
        ports = self.inspect()['NetworkSettings']['Ports']
        if not ports:
            return None
        elif port_name not in ports:
            return None
        return ports[port_name][0]["HostPort"]

    def test_connection(self, timeout=1):
        """
        Checks if the service running inside the container is accepting connections
        """
        if not self.service_port:
            raise NotReachableException("Could not find container port")
        if not self.internal_ip:
            raise NotReachableException("Could not find container IP, is container running?")

        return test_tcp_connection(self.internal_ip, self.service_port)

    def wait_for_service_listening(self):
        tries = 0
        while tries < 30:
            if self.test_connection():
                return
            sleep(5)
            tries += 1

        raise DBTimeoutException("Could not connect with database, max retries reached")

    def _make_container_name(self, template, name):
        container_name = settings.CONTAINER_PREFIX + template
        if name:
            container_name += '-' + name
        return container_name


class AbstractDatabaseTemplate(AbstractDatabase):
    """
    Abstract implementation of a template database
    """

    not_found_exception_class = NonExistentTemplate

    def __init__(self, docker_client, template, create=False):
        super().__init__(docker_client, template, None, create)

    def clone(self, name):
        if self.running():
            raise ImportInProgress

        database = self.database_backend(self.client, self.template, name, create=True)

        template_data_path = join_path(self.host_datadir, '.')

        copy_tree(template_data_path, database.host_datadir)

        return database

    @abstractmethod
    def import_data(self, sql_file):
        pass

    @abstractmethod
    def get_engine_status(self):
        pass

    @abstractproperty
    def database_backend(self):
        pass

    @property
    def labels(self):
        return {
            'com.myaas.is_template': 'True',
            'com.myaas.provider': self.provider_name,
            'com.myaas.template': self.template,
        }

    @property
    def restart_policy(self):
        return {"MaximumRetryCount": 0, "Name": "no"}
