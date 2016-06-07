import os
import unittest

from launcher import settings
from launcher.utils.container import client
from launcher.backends import AbstractDatabase
from launcher.backends.mysql import MysqlDatabase


class AbstractDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.client = client

    def tearDown(self):
        self.client.close()

    def test_cannot_construct(self):
        self.assertRaises(Exception, lambda: AbstractDatabase(self.client, 'base'))


class MysqlDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.client = client

    def tearDown(self):
        self.client.close()

    @classmethod
    def tearDownClass(cls):
        db = MysqlDatabase(client, 'base')
        db.purge()

    def test_construct(self):
        assert issubclass(MysqlDatabase, AbstractDatabase)
        db = MysqlDatabase(self.client, 'base')
        assert isinstance(db, MysqlDatabase)
        assert isinstance(db, AbstractDatabase)

    def test_paths(self):
        db = MysqlDatabase(self.client, 'base')
        # this is the path to db data as seen from the launcher
        assert db.container_path.startswith(settings.DATA_DIR)
        # this is the real path on the docker host
        assert db.host_path.startswith(settings.HOST_DATA_DIR)

    def test_start_stop_db(self):
        db = MysqlDatabase(self.client, 'base')
        if db.running():
            db.stop()

        db.start()
        assert db.running()
        db.stop()
        assert not db.running()

    def test_purge_db(self):
        db = MysqlDatabase(self.client, 'base')
        db.start()
        db.wait_until_active()
        assert os.path.isdir(db.container_path)
        db.purge()
        assert not os.path.isdir(db.container_path)

    def test_port_mapping(self):
        db = MysqlDatabase(self.client, 'base')
        db.start()
        assert db.external_port is not None


if __name__ == '__main__':
    unittest.main()
