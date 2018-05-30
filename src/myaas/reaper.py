import signal
import logging
import sys
import re
from time import sleep
from datetime import datetime

import click

from .settings import DEBUG
from .utils.database import get_myaas_containers, get_enabled_backend
from .utils.container import client


logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
    level=logging.DEBUG if DEBUG else logging.INFO)

logger = logging.getLogger("myaas-reaper")


def get_container_name(container):
    return container['Names'][0].lstrip('/')


class SignalHandler:
    def __init__(self):
        self.__killed = False
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

    @property
    def exit(self):
        return self.__killed

    def stop(self, signum, frame):
        self.__killed = True


class ContainerFilter(object):
    def __init__(self, expired=False, dead=False, unhealthy=False):
        self._expired = expired
        self._regex = False
        if isinstance(expired, str):
            self._expired = re.compile(expired)
            self._regex = True
        self._dead = dead
        self._unhealthy = unhealthy

    def filter(self, containers):
        if self._expired:
            logger.info('* Filtering expired')
        if self._dead:
            logger.info('* Filtering exited')
        if self._unhealthy:
            logger.info('* Filtering unhealthy')
        return filter(self._is_removable, containers)

    def _is_removable(self, container):
        name = get_container_name(container)
        if self._expired and self._is_expired(container):
            logger.info("%s is expired, queued for deletion", name)
            return True

        if self._dead and self._is_dead(container):
            logger.info("%s is dead, queued for deletion", name)
            return True

        if self._unhealthy and self._is_unhealthy(container):
            logger.info("%s is unhealthy, queued for deletion", name)
            return True

        return False

    def _is_expired(self, container):
        if 'com.myaas.expiresAt' in container['Labels']:
            expiry_ts = round(float(container['Labels']['com.myaas.expiresAt']))  # noqa
        else:
            # asume a 24 hours TTL
            expiry_ts = int(container['Created']) + 86400

        expired = datetime.utcnow() >= datetime.utcfromtimestamp(expiry_ts)

        if expired and self._regex:
            container_name = container['Labels']['com.myaas.instance']
            return bool(self._expired.match(container_name))

        return expired

    def _is_dead(self, container):
        return container['State'] == 'exited'

    def _is_unhealthy(self, container):
        return 'unhealthy' in container['Status']


def remove_database(container):
    template = container['Labels']['com.myaas.template']
    name = container['Labels']['com.myaas.instance']
    try:
        logger.info(f'removing {name}')
        backend = get_enabled_backend().Database
        backend(client, template, name).remove()
    except Exception as e:
        logger.exception(
            f"Failed to remove database {template} {name}")


@click.command()
@click.option('-e', '--expired', is_flag=True, default=False, help='Remove expired containers.')
@click.option('--expired-regex', default=False, help="Remove expired containers only if instance name matches regex, implies -e")
@click.option('-d', '--dead', is_flag=True, default=False, help='Remove exited containers.')
@click.option('-u', '--unhealthy', is_flag=True, default=False, help='Remove unhealthy containers.')
@click.option('--dry-run', is_flag=True, default=False, help='Only print name of containers that would be removed and exit.')
def cleanup(expired, expired_regex, dead, unhealthy, dry_run):
    if not (expired or expired_regex or dead or unhealthy):
        raise click.UsageError("at least one filter must be enabled, use --help for more information")

    try:
        cf = ContainerFilter(expired_regex or expired, dead, unhealthy)
    except re.error:
        click.echo(click.style("regex is not valid", fg="red"))
        sys.exit(1)

    databases = cf.filter(get_myaas_containers())

    if dry_run:
        logger.info("Started in dry mode")
        for d in databases:
            name = get_container_name(d)
            logger.info("would remove %s", name)
        return

    logger.info("Starting myaas ttl reaper...")
    sighandler = SignalHandler()
    while not sighandler.exit:
        databases = cf.filter(get_myaas_containers())
        for d in databases:
            remove_database(d)
        sleep(1)

    logger.info("Stopped")


if __name__ == '__main__':
    cleanup()
