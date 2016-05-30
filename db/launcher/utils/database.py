import docker
import logging
import os
from subprocess import call

from .container import find_container, list_containers, client
from .. import settings
from ..backends.mysql import MysqlDatabase

logger = logging.getLogger(__name__)


class ImportInProgress(Exception):
    pass


def list_databases():
    containers = filter(_is_database_container, list_containers())
    return [_get_database_name(c) for c in containers]


def list_database_templates():
    containers = filter(_is_template_container, list_containers())
    return [_get_database_name(c) for c in containers]


def get_database(template, name):
    name = '{template}-{name}'.format(**locals())
    container = find_container(settings.CONTAINER_PREFIX + name)
    if not container:
        return None
    return MysqlDatabase(client, name)


def database_from_template(template, name):
    client = docker.Client()
    template_db = MysqlDatabase(client, template)
    if template_db.running():
        raise ImportInProgress
    database = MysqlDatabase(client, template, name)
    # reflink=auto will use copy on write if supported
    copy_command = ["cp", "-r", "--reflink=auto",
                    os.path.join(template_db.datadir_launcher, '.'),
                    database.datadir_launcher]
    logger.debug(copy_command)
    call(copy_command)
    return database


def _is_database_container(container):
    if 'com.myaas.instance' not in container['Labels']:
        return False

    return container['Labels'].get('com.myaas.instance') != ''


def _is_template_container(container):
    if 'com.myaas.is_template' not in container['Labels']:
        return False

    return container['Labels'].get('com.myaas.is_template') == 'True'


def _count_dashes(name):
    splits = name.split('-')
    return len(splits)


def _get_database_name(container):
    labels = container['Labels']
    return "%s,%s" % (labels['com.myaas.template'], labels['com.myaas.instance'])
