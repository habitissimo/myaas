import os
import subprocess

from . import settings
from .backends.mysql import MysqlDatabase
from .utils.container import client


def list_dump_files():
    files_in_dir = os.listdir(settings.DUMP_DIR)
    return set(filter(lambda x: x.endswith('.sql'), files_in_dir))


def indent(string, level=1):
    spacing = "  " * level
    return spacing + string


def start_database(name):
    print("- Found database {}".format(name))
    db = MysqlDatabase(client, name=name)
    if not db.running():
        print(indent("* Not running, starting..."))
        db.start()
        db.wait_until_active()
    print(indent("* OK"))
    return db


def stop_database(database):
    print(indent("* Stopping database..."))
    database.stop()
    print(indent("* Stopped"))


def import_database(db, dump):
    print(indent("* Importing data..."))
    mysql_command = ["mysql",
                     "--user={}".format(db.user),
                     "--password={}".format(db.password),
                     "--host={}".format(db.internal_ip),
                     "--port={}".format(db.internal_port),
                     db.database]

    with open(dump, 'r') as f:
        proc = subprocess.Popen(mysql_command, stdin=f)
        out, err = proc.communicate()


def main():
    dumps = list_dump_files()
    for dump in dumps:
        db_name = dump[:-4]  # strip .sql from the name
        try:
            db = start_database(db_name)
            import_database(db, os.path.join(settings.DUMP_DIR, dump))
            stop_database(db)
        except:
            pass


if __name__ == "__main__":
    main()
