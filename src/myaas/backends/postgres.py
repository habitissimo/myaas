import os

from .. import settings
from .base import AbstractDatabase, AbstractDatabaseTemplate
from .exceptions import ImportDataError


class Database(AbstractDatabase):
    @property
    def provider_name(self):
        return "postgres"

    @property
    def datadir(self):
        return "/var/lib/postgresql/data"

    @property
    def environment(self):
        return settings.POSTGRES_ENVIRONMENT

    @property
    def image(self):
        return settings.POSTGRES_IMAGE

    @property
    def service_port(self):
        return 5432

    @property
    def user(self):
        return "postgres"

    @property
    def password(self):
        return settings.POSTGRES_ENVIRONMENT['POSTGRES_PASSWORD']

    @property
    def database(self):
        return settings.POSTGRES_ENVIRONMENT['POSTGRES_DB']

    @property
    def mem_limit(self):
        return '3g'


class Template(Database, AbstractDatabaseTemplate):
    @property
    def database_backend(self):
        return Database

    def import_data(self, pg_dump):
        command = self._build_pg_command()
        env = os.environ.copy()
        env['PGPASSWORD'] = self.password
        with open(pg_dump, 'r') as f:
            out, err = self._run_command(command, stdin=f, env=env)
            if err:
                raise ImportDataError(err)

    def get_engine_status(self):
        pass

    def _build_pg_command(self):
        return ["psql",
                "--username={}".format(self.user),
                "--host={}".format(self.internal_ip),
                "--port={}".format(self.service_port),
                self.database]
