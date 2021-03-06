import logging
import importlib

from .. import settings
from .container import list_containers

logger = logging.getLogger(__name__)


def get_enabled_backend():
    return importlib.import_module(settings.BACKEND)


def get_myaas_containers():
    return filter(_is_database_container, list_containers())


def list_databases():
    containers = filter(_is_database_container, list_containers())
    return [_get_database_name(c) for c in containers]


def list_database_templates():
    containers = filter(_is_template_container, list_containers())
    return [_get_database_name(c) for c in containers]


def _is_database_container(container):
    if not container['Labels']:
        return False

    if 'com.myaas.instance' not in container['Labels']:
        return False

    return container['Labels'].get('com.myaas.instance') != ''


def _is_template_container(container):
    if not container['Labels']:
        return False

    if 'com.myaas.is_template' not in container['Labels']:
        return False

    return container['Labels'].get('com.myaas.is_template') == 'True'


def _get_database_name(container):
    labels = container['Labels']
    if labels['com.myaas.is_template'] == 'True':
        return labels['com.myaas.template']
    else:
        return "%s,%s" % (labels['com.myaas.template'], labels['com.myaas.instance'])
