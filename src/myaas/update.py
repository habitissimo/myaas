import os
import sys
import traceback

from docker.errors import NotFound as ImageNotFound

from . import settings
from .utils.container import client
from .utils.database import get_enabled_backend
from .utils.filesystem import is_empty
from .utils.retry import RetryPolicy
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
    backend = get_enabled_backend().Template
    try:
        db = backend(client, template, False)
        if db.running():
            db.stop()
        db.do_backup(use_rename=True)
        db.remove()
    except NonExistentTemplate:
        pass  # this means this database is being imported for the first time

    try:
        database = backend(client, template, True)
    except ImageNotFound as e:
        import sys
        print("\n### ERROR ###", file=sys.stderr)
        print(e.explanation.decode(), file=sys.stderr)
        print("Pull the image and try again.", file=sys.stderr)
        sys.exit(1)

    return database


def start_template_database(db_name):
    print("- Creating database {}".format(db_name))
    db = remove_recreate_database(db_name)

    print(indent("* Starting database..."))
    db.start()
    print(indent("* Started"))
    print(indent("* Waiting for database to accept connections"))
    try:
        db.wait_for_service_listening()
        return db
    except:
        print(indent(
            f"* Max time waiting for database exceeded"
            ", retrying {tried} of {max_tries}..."
        ))
        db.stop()
        db.restore_backup()
        print_exception()
        return False


def main():
    dumps = list_dump_files()
    for dump in dumps:
        db_name = dump[:-4]  # strip .sql from the name
        sql_file = os.path.join(settings.DUMP_DIR, dump)

        if is_empty(sql_file):
            print(f"- Skipping: {sql_file} is empty")
            continue

        start_db_func = partial(start_template_database, db_name)
        db = RetryPolicy(5, delay=2)(start_db_func)
        if not db:
            continue # skip to next database to import

        print(indent("* Importing data..."))
        try:
            db.import_data(sql_file)
            db.remove_backup()
        except ImportDataError:
            print(indent("* An error happened, debug information:", level=2))
            print(db.get_engine_status(), file=sys.stderr)
            print(indent("* Restoring previous database", level=2))
            db.stop()
            db.restore_backup()
            print_exception()
            continue

        print(indent("* Stopping database..."))
        db.stop()
        print(indent("* Stopped"))


if __name__ == "__main__":
    main()
