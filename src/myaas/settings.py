from decouple import config

DEBUG = config('DEBUG', default=False, cast=bool)
HOSTNAME = config('HOST_NAME')

# Docker socket address, can be replaced with a TCP address iy you prefer not
# to bind mount the docker socket
DOCKER_SOCKET = config("DOCKER_SOCKET", default="unix://var/run/docker.sock")

HOST_DATA_DIR = config("HOPS_DATA_DIR", default="/opt/hops/db/data")
HOST_DUMP_DIR = config("HOPS_DUMP_DIR", default="/opt/hops/db/dumps")
DATA_DIR = "/hops/db/data"
DUMP_DIR = "/hops/db/dumps"

# All containers created by this service will have this prefix in their name
CONTAINER_PREFIX = 'myaas-'

# Default docker imgage for the mysql backend
# Currently tested with:
#  - mariadb:10
#  - mysql:5
#  - habitissimo/myaas-mysql:10.1 (based on mariadb:10)
MYSQL_IMAGE = config("MYSQL_IMAGE", default="habitissimo/myaas-mysql:10.1")

# Required environment variables for running the mysql image
# All of the listed images above need this environemnt variables
MYSQL_ENVIRONMENT = {
    "MYSQL_ROOT_PASSWORD": config("MYSQL_ROOT_PASSWORD", default="secret"),
    "MYSQL_DATABASE": config("MYSQL_DATABASE", default="default"),
}
