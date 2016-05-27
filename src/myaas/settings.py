from decouple import config

# Backend to enable, valid choices are:
# "myaas.backends.mysql"
# "myaas.backends.postgres"
BACKEND = config("BACKEND", default="myaas.backends.mysql")


# Controls the debug mode of the application
DEBUG = config('DEBUG', default=False, cast=bool)

# Docker socket address, can be replaced with a TCP address iy you prefer not
# to bind mount the docker socket
DOCKER_SOCKET = config("DOCKER_SOCKET", default="unix://var/run/docker.sock")

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

POSTGRES_IMAGE = config("POSTGRES_IMAGE", default="postgres:9.4")
POSTGRES_ENVIRONMENT = {
    "POSTGRES_PASSWORD": config("POSTGRES_PASSWORD", default="secret"),
    "POSTGRES_USER": config("POSTGRES_USER", default="postgres"),
    "POSTGRES_DB": config("POSTGRES_DB", default="postgres"),
}


# Enable CPU pinning for created containers
CPU_PINNING = config("CPU_PINNING", default=True, cast=bool)
# How many CPUs to assign to every container
CPU_PINNING_INSTANCE_CORES = config("CPU_PINNING_INSTANCE_CORES", default=2, cast=int)

# Internal settings
HOSTNAME = config('HOST_NAME', default='localhost')
BASE_DIR = config('BASE_DIR', default='/myaas')
DATA_DIR = BASE_DIR + "/data"
DUMP_DIR = BASE_DIR + "/dumps"
