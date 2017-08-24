from time import sleep
from datetime import datetime
import signal
import logging
import os

from .utils.database import (
    get_myaas_containers,
    get_enabled_backend,
)
from .utils.container import client
from .settings import DEBUG


logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)s: %(message)s'.format(os.getpid()),
    level=logging.DEBUG if DEBUG else logging.INFO)
logging.getLogger('requests').setLevel(logging.CRITICAL)
logging.getLogger('docker').setLevel(logging.CRITICAL)
logger = logging.getLogger("myaas-reaper")


class SignalHandler:
    __should_run = True
    __registered = False

    @property
    def should_run(self):
        return self.__should_run

    def __init__(self):
        if not self.__registered:
            self.register_signals()

    def stop(self, signum, frame):
        self.__should_run = False

    def register_signals(self):
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)


class TtlReaper():

    def __init__(self, sighandler):
        self.sighandler = sighandler

    def remove_container(self, template, name):
        logger.info(f'removing {name}')
        database_class = get_enabled_backend().Database
        db = database_class(client, template, name)
        db.remove()

    def _expired(self, container):
        if 'com.myaas.expiresAt' in container['Labels']:
            expiry_ts = round(float(container['Labels']['com.myaas.expiresAt']))  # noqa
        else:
            # asume a 24 hours TTL
            expiry_ts = int(container['Created']) + 86400

        return datetime.utcnow() >= datetime.utcfromtimestamp(expiry_ts)

    def _exited(self, container):
        return container['State'] == 'exited'

    def _unhealthy(self, container):
        return 'unhealthy' in container['Status']

    def cleanup_containers(self):
        for c in get_myaas_containers():
            template = c['Labels']['com.myaas.template']
            name = c['Labels']['com.myaas.instance']

            if self._exited(c) or self._expired(c) or self._unhealthy(c):
                try:
                    self.remove_container(template, name)
                except Exception as e:
                    logger.exception(
                        f"Failed to remove container {template} {name}")

    def start(self):
        logger.info("Starting myaas ttl reaper...")
        while self.sighandler.should_run:
            self.cleanup_containers()
            sleep(10)

    def __call__(self):
        self.start()


if __name__ == '__main__':
    sighandler = SignalHandler()
    daemon = TtlReaper(sighandler)
    daemon.start()
