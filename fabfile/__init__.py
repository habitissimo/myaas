import os
import dotenv

from fabric.api import env
from fabric import state

from db import DBProvider


state.output['running'] = False
state.output['stdout'] = False


def load_dotenv():
    current_path = os.path.abspath(os.path.dirname(__file__))
    dotenv_file = os.path.join(current_path, ".env")
    if os.path.isfile(dotenv_file):
        dotenv.load_dotenv(dotenv_file)

def check_conf():
    if not env.db_multiplexer_url:
        print "DB_URL environment variables is not defined."
        import sys
        sys.exit(1)

load_dotenv()
env.db_multiplexer_url = os.getenv('DB_URL')
check_conf()
db = DBProvider().expose_as_module('db')
