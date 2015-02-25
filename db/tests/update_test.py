import unittest
from mock import patch

from launcher.update import list_dump_files


DATABASE_NAMES = ['ar', 'br', 'cl', 'co', 'es', 'it', 'mx', 'pt']
SQL_FILES, BZIP_FILES = zip(*((n + '.sql', n + '.sql.bz2') for n in DATABASE_NAMES))


class UpdateDatabaseTest(unittest.TestCase):
    def test_list_dump_files(self):
        with patch('os.listdir', return_value=SQL_FILES + BZIP_FILES):
            files = list_dump_files()
        assert files == set(SQL_FILES)


if __name__ == '__main__':
    unittest.main()
