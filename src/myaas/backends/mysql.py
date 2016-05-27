import pymysql

from .. import settings

from .base import AbstractDatabase, AbstractDatabaseTemplate
from .exceptions import ImportDataError


class Database(AbstractDatabase):
    @property
    def provider_name(self):
        return "mysql"

    @property
    def datadir(self):
        return "/var/lib/mysql"

    @property
    def environment(self):
        return settings.MYSQL_ENVIRONMENT

    @property
    def image(self):
        return settings.MYSQL_IMAGE

    @property
    def service_port(self):
        return 3306

    @property
    def user(self):
        return "root"

    @property
    def password(self):
        return settings.MYSQL_ENVIRONMENT['MYSQL_ROOT_PASSWORD']

    @property
    def database(self):
        return settings.MYSQL_ENVIRONMENT['MYSQL_DATABASE']

    @property
    def memory_limit(self):
        return '3g'

    def test_connection(self):
        super().test_connection()
        try:
            conn = pymysql.connect(
                host=self.internal_ip,
                port=self.service_port,
                user=self.user,
                passwd=self.password,
                db=self.database)
            conn.close()
        except pymysql.OperationalError:
            return False

        return True


class Template(Database, AbstractDatabaseTemplate):
    @property
    def database_backend(self):
        return Database

    def import_data(self, sql_file):
        mysql_command = self._build_mysql_command()
        with open(sql_file, 'r') as f:
            out, err = self._run_command(mysql_command, stdin=f)
            if err:
                raise ImportDataError(err)

    def get_engine_status(self):
        mysql_command = self._build_mysql_command()
        mysql_command.append("-e")
        mysql_command.append("show engine innodb status\G")
        out, err = self._run_command(mysql_command)
        return out

    def _build_mysql_command(self):
        return ["mysql",
                "--user={}".format(self.user),
                "--password={}".format(self.password),
                "--host={}".format(self.internal_ip),
                "--port={}".format(self.service_port),
                self.database]
