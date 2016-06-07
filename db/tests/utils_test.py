import os
import unittest

from launcher.utils.container import client
from launcher.backends.mysql import MysqlDatabase
from launcher.utils.database import (
    list_databases,
    list_database_templates,
    database_from_template)


TEST_TEMPLATES = ['template1', 'template2']
TEST_DATABASES = ['template1-develop', 'template2-master']


class UtilsDatabaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = client
        # spawn some dbs
        for name in TEST_TEMPLATES + TEST_DATABASES:
            db = MysqlDatabase(cls.client, name)

    @classmethod
    def tearDownClass(cls):
        for name in TEST_TEMPLATES + TEST_DATABASES:
            db = MysqlDatabase(cls.client, name)
            db.purge()
        cls.client.close()

    def test_list_databases(self):
        databases = list_databases()
        # exclude other posible existent names
        databases = set(databases) & set(TEST_DATABASES)
        assert databases == set(TEST_DATABASES)

    def test_list_database_templates(self):
        templates = list_database_templates()
        # exclude other posible existent names
        templates = set(templates) & set(TEST_TEMPLATES)
        assert templates == set(TEST_TEMPLATES)

    def test_database_from_template(self):
        template, name = ('template1', 'copy')

        # data for template will not exists if database hasn't been
        # started at least once
        db_template = MysqlDatabase(self.client, template)
        db_template.start()
        db_template.wait_until_active()

        # calculate the path wich will be assigned to the new database
        data_dir = db_template.container_path + '-' + name

        assert not os.path.isdir(data_dir)
        database = database_from_template(template, name)
        database.start()
        database.wait_until_active()

        # check assigned datadir matched the calculated
        assert database.container_path == data_dir
        # check datadir was created
        assert os.path.isdir(data_dir)

        # cleanup
        database.purge()


if __name__ == '__main__':
    unittest.main()
