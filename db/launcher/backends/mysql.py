import pymysql

from . import AbstractDatabase
from .. import settings


class MysqlDatabase(AbstractDatabase):

    @property
    def datadir_database(self):
        return "/var/lib/mysql"

    @property
    def environment(self):
        return settings.MYSQL_ENVIRONMENT

    @property
    def image(self):
        return settings.MYSQL_DOCKER_IMAGE

    @property
    def internal_port(self):
        return 3306

    @property
    def password(self):
        return settings.MYSQL_ENVIRONMENT['MYSQL_ROOT_PASSWORD']

    @property
    def mem_limit(self):
        return '3g'

    def clone(self):
        pass

    def test_connection(self):
        super().test_connection()
        try:
            conn = pymysql.connect(
                host=self.internal_ip,
                port=self.internal_port,
                user=self.user,
                passwd=self.password,
                db=self.database)
            conn.close()
        except pymysql.OperationalError:
            return False

        return True
