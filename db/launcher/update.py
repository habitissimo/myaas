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


def remove_recreate_database(name):
    # find existing database, remove it, then recreate
    db = MysqlDatabase(client, name=name)
    db.purge()
    # recreate
    db = MysqlDatabase(client, name=name)
    print("- Creating database {}".format(name))

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


def build_mysql_command(db):
    return ["mysql",
            "--user={}".format(db.user),
            "--password={}".format(db.password),
            "--host={}".format(db.internal_ip),
            "--port={}".format(db.internal_port),
            db.database]


def run_command(command, stdin=None):
    proc = subprocess.Popen(command,
                            stdin=stdin,
                            stderr=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            universal_newlines=True)
    out, err = proc.communicate()
    return (out, err)


def import_database(db, dump):
    print(indent("* Importing data..."))
    mysql_command = build_mysql_command(db)

    with open(dump, 'r') as f:
        out, err = run_command(mysql_command, stdin=f)
        if err:
            print(indent("* An error happened, debug information:", level=2))
            print(get_engine_status(db))


def get_engine_status(db):
    mysql_command = build_mysql_command(db)
    mysql_command.append("-e")
    mysql_command.append("show engine innodb status\G")
    out, err = run_command(mysql_command)
    return out


def main():
    dumps = list_dump_files()
    for dump in dumps:
        db_name = dump[:-4]  # strip .sql from the name
        try:
            db = remove_recreate_database(db_name)
            import_database(db, os.path.join(settings.DUMP_DIR, dump))
            stop_database(db)
        except:
            pass


if __name__ == "__main__":
    main()
