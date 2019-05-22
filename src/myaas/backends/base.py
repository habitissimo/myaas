import logging
import subprocess

from abc import ABCMeta, abstractmethod, abstractproperty
from os.path import isdir, join as join_path
from time import sleep
from datetime import datetime, timedelta
import docker

from .. import settings
from ..utils.container import (
    find_container, translate_host_basedir,
    get_random_cpuset, get_mapped_cpuset
)
from ..utils.socket import reserve_port, test_tcp_connection
from ..utils.btrfs import FileSystem

from .exceptions import (NonExistentDatabase, NonExistentTemplate,
                         NotReachableException, DBTimeoutException,
                         ImportInProgress, ContainerRunning)


logger = logging.getLogger(__name__)


class ContainerService():
    """
    Convenience wrappers arround docker client API
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
        if settings.CPU_MAP:
            return get_mapped_cpuset()
        if not settings.CPU_PINNING_INSTANCE_CORES == 0:
            return get_random_cpuset(settings.CPU_PINNING_INSTANCE_CORES)
        return None

    @property
    def memory_limit(self):
        return settings.MEMORY_LIMIT

    @property
    def restart_policy(self):
        return None

    def start(self):
        fs = FileSystem(settings.DATA_DIR)
        subvolume = fs.find_subvolume_by_name(self.container_name)
        if not subvolume:
            fs.make_subvolume(self.container_name)

        self.client.start(self.container)

    def stop(self):
        self.client.stop(self.container, timeout=5)
        self.client.wait(self.container)

    def kill(self):
        self.client.kill(self.container)

    def running(self):
        return self.inspect()['State']['Running']

    def remove(self):
        if self.running():
            self.stop()

        try:
            self.client.remove_container(self.container, v=True, force=True)
        except docker.errors.NotFound:
            # the reaper may already have kicked in to delete the stoped container
            pass
        except docker.errors.APIError:
            # removal already in progress
            pass

        self.container = None

    def inspect(self):
        return self.client.inspect_container(self.container)

    def make_host_config(self):
        return {
            "port_bindings": {port: reserve_port() for port in self.ports},
            "mem_limit": '11G',
            "restart_policy": self.restart_policy,
            "oom_kill_disable": True,
        }

    def create_container(self, image):
        host_config = self.make_host_config()
        # remove empty properties from config dict
        host_config = {k: v for k, v in host_config.items() if v}
        container = self.client.create_container(
            image=image,
            name=self.container_name,
            ports=self.ports,
            volumes=self.volumes,
            environment=self.environment,
            labels=self.labels,
            cpuset=self.cpuset,
            host_config=self.client.create_host_config(**host_config))

        self.client.update_container(container, mem_reservation=self.memory_limit)

        return container


class PersistentContainerService(ContainerService):
    @property
    def datadir(self):
        return "/tmp"

    @property
    def backup_name(self):
        return 'backup-' + self.container_name

    @property
    def backup_path(self):
        return join_path(settings.DATA_DIR, self.backup_name)

    @property
    def host_datadir(self):
        return join_path(settings.DATA_DIR, self.container_name)

    @property
    def volumes(self):
        return [self.datadir]

    def remove(self):
        super().remove()
        if isdir(self.host_datadir):
            fs = FileSystem(settings.DATA_DIR)
            fs.delete_subvolume(self.container_name)

    def make_bindings_config(self):
        # host_datadir needs to be translated as the docker daemon runs on the
        # host and does not see the host directories trough a binded volume
        host_datadir = translate_host_basedir(self.host_datadir)
        return {host_datadir: {'bind': self.datadir, 'ro': False}}

    def make_host_config(self):
        config = super().make_host_config()
        config['binds'] = self.make_bindings_config()
        return config

    def do_backup(self):
        if self.running():
            raise ContainerRunning()

        # remove previous backup if exists
        self.remove_backup()

        if not isdir(self.host_datadir):
            return  # nothing to backup

        fs = FileSystem(settings.DATA_DIR)
        subvolume = fs.find_subvolume_by_name(self.container_name)
        subvolume.take_snapshot(self.backup_name)

    def remove_backup(self):
        if isdir(self.backup_path):
            fs = FileSystem(settings.DATA_DIR)
            subvolume = fs.delete_subvolume(self.backup_name)

    def restore_backup(self):
        if self.running():
            raise ContainerRunning()

        if not isdir(self.backup_path):
            return False

        fs = FileSystem(settings.DATA_DIR)
        fs.delete_subvolume(self.container_name)
        subvolume = fs.find_subvolume_by_name(self.backup_name)
        subvolume.take_snapshot(self.container_name)
        fs.delete_subvolume(self.backup_name)

        return True


class AbstractDatabase(PersistentContainerService, metaclass=ABCMeta):
    """Abstract implementation for a database backend"""

    WAIT_MAX_TRIES = 30
    not_found_exception_class = NonExistentDatabase

    def __init__(self, client, template, name, create=False, ttl=settings.CONTAINER_TTL):  # noqa
        container_name = self._make_container_name(template, name)

        super().__init__(client, container_name)

        self.template = template
        self.name = name
        self.create = create
        self.ttl = int(ttl)

        if not self.container:
            if not self.create:
                raise self.not_found_exception_class()
            self.container = self.create_container(self.image)

    @property
    def user(self):
        return ''

    @property
    def password(self):
        return ''

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
        return {"MaximumRetryCount": 5, "Name": "on-failure"}

    @property
    def ports(self):
        return [self.service_port]

    @property
    def labels(self):
        labels = {
            'com.myaas.provider': self.provider_name,
            'com.myaas.is_template': 'False',
            'com.myaas.template': self.template,
            'com.myaas.instance': self.name,
            'com.myaas.username': self.user,
            'com.myaas.password': self.password,
        }
        if self.ttl and self.ttl > 0:
            expire_at = datetime.now() + timedelta(seconds=self.ttl)
            labels.update({'com.myaas.expiresAt': str(expire_at.timestamp())})
        return labels

    @property
    def host_port(self):
        port_name = f'{self.service_port}/tcp'
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
        while tries < self.WAIT_MAX_TRIES:
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
    WAIT_MAX_TRIES = 60

    not_found_exception_class = NonExistentTemplate

    def __init__(self, docker_client, template, create=False):
        super().__init__(docker_client, template, None, create, ttl=0)

    def clone(self, name, ttl=None):
        if self.running():
            raise ImportInProgress

        database = self.database_backend(
            self.client, self.template,
            name, create=True, ttl=ttl)

        fs = FileSystem(settings.DATA_DIR)

        pre_existent_volume = fs.find_subvolume_by_name(database.container_name)
        if pre_existent_volume:
            pre_existent_volume.delete()

        subvolume = fs.find_subvolume_by_name(self.container_name)
        subvolume.take_snapshot(database.host_datadir)

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

    def _run_command(self, command, stdin=None, env=None):
        proc = subprocess.Popen(command,
                                stdin=stdin,
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                universal_newlines=True,
                                env=env)
        out, err = proc.communicate()
        return (out, err)
