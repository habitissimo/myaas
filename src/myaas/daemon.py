import threading
from time import sleep
from datetime import datetime
import signal

from .utils.database import (
    get_myaas_containers,
    get_enabled_backend,
)
from .utils.container import client


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
        print("STOPPING.....")
        self.__should_run = False

    def register_signals(self):
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)


class Daemon():

    def __init__(self, sighandler):
        self.sighandler = sighandler

    def remove_container(self, template, name):
        database_class = get_enabled_backend().Database
        db = database_class(client, template, name)
        db.remove()

    def remove_expired_containers(self):
        containers = get_myaas_containers()
        now = datetime.utcnow()
        for container in containers:
            labels = container['Labels']
            if 'com.myaas.expiresAt' not in labels:
                continue
            expires_at = labels['com.myaas.expiresAt']
            expires_at = datetime.utcfromtimestamp(float(expires_at))
            template= labels['com.myaas.template']
            name = labels['com.myaas.instance']
            if now >= expires_at:
                self.remove_container(template, name)

    def start(self):
        while self.sighandler.should_run:
            self.remove_expired_containers()
            sleep(1)

    def __call__(self):
        self.start()


if __name__ == '__main__':
    sighandler = SignalHandler()
    daemon = Daemon(sighandler)
    daemon_thread = threading.Thread(
        name='myaas_daemon', target=daemon)
    daemon_thread.setDaemon(False)
    daemon_thread.start()
