import docker
from subprocess import call

from .container import find_container, list_containers, client
from .. import settings
from ..backends.mysql import MysqlDatabase


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
        template_db.stop()
    database = MysqlDatabase(client, '%s-%s' % (template, name))
    # reflink=auto will use copy on write if supported
    call(["cp", "-r", "--reflink=auto",
         template_db.datadir_launcher, database.datadir_launcher])
    return database


def _is_hops_db_container(container):
    names = container['Names']
    if not names:
        return False
    return names[0].startswith('/{}'.format(settings.CONTAINER_PREFIX))


def _is_database_container(container):
    if not _is_hops_db_container(container):
        return False
    return _count_dashes(container['Names'][0]) == 3


def _is_template_container(container):
    if not _is_hops_db_container(container):
        return False
    return _count_dashes(container['Names'][0]) == 2


def _count_dashes(name):
    splits = name.split('-')
    return len(splits)


def _get_database_name(container):
    name = container['Names'][0]
    # remove / from the start
    name = name[1:]
    # remove prefix
    name = name[len(settings.CONTAINER_PREFIX):]
    return name
