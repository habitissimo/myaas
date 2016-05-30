import os

FLASK_DEBUG = os.getenv('DEBUG', False)
HOSTNAME = os.getenv('HOST_NAME')

MYSQL_DOCKER_IMAGE = os.getenv("MYSQL_DOCKER_IMAGE")
MYSQL_ROOT_USER = 'root'
MYSQL_ROOT_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "default")
DOCKER_SOCKET = os.getenv("DOCKER_SOCKET")

HOST_DATA_DIR = os.getenv("HOPS_DATA_DIR")
HOST_DUMP_DIR = os.getenv("HOPS_DUMP_DIR")
DATA_DIR = "/hops/db/data"
DUMP_DIR = "/hops/db/dumps"

CONTAINER_PREFIX = 'myaas-'

# Required environemnt to execute library/mariadb:latest
MYSQL_ENVIRONMENT = {
    "MYSQL_ROOT_PASSWORD": MYSQL_ROOT_PASSWORD,
    "MYSQL_USER": "not_used",
    "MYSQL_PASSWORD": "not_used",
    "MYSQL_DATABASE": MYSQL_DATABASE,
}
