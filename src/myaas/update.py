import os
import sys
import traceback

from . import settings
from .utils.container import client
from .backends.mysql import MysqlDatabaseTemplate
from .backends.exceptions import NonExistentTemplate, ImportDataError


def list_dump_files():
    files_in_dir = os.listdir(settings.DUMP_DIR)
    return set(filter(lambda x: x.endswith('.sql'), files_in_dir))


def indent(string, level=1):
    spacing = "  " * level
    return spacing + string


def print_exception():
    print('-' * 80)
    traceback.print_exc(file=sys.stderr)
    print('-' * 80)


def remove_recreate_database(template):
    """
    find existing database, remove it, then recreate
    """
    try:
        db = MysqlDatabaseTemplate(client, template, False)
        db.backup_datadir(move=True)
        db.destroy()
    except NonExistentTemplate:
        pass  # this means this database is being imported for the first time

    return MysqlDatabaseTemplate(client, template, True)


def main():
    dumps = list_dump_files()
    for dump in dumps:
        db_name = dump[:-4]  # strip .sql from the name
        sql_file = os.path.join(settings.DUMP_DIR, dump)

        print("- Creating database {}".format(db_name))
        db = remove_recreate_database(db_name)

        print(indent("* Starting database..."))
        db.start()
        print(indent("* Started"))

        try:
            print(indent("* Waiting for database to accept connections"))
            db.wait_until_active()
        except:
            db.stop()
            db.restore_datadir()
            print_exception()
            continue

        print(indent("* Importing data..."))
        try:
            db.import_data(sql_file)
            db.remove_backup()
        except ImportDataError:
            print(indent("* An error happened, debug information:", level=2))
            print(db.get_engine_status(), file=sys.stderr)
            print(indent("* Restoring previous database", level=2))
            db.stop()
            db.restore_datadir()
            print_exception()
            continue

        print(indent("* Stopping database..."))
        db.stop()
        print(indent("* Stopped"))


if __name__ == "__main__":
    main()
