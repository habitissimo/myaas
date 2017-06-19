from decouple import config

# Backend to enable, valid choices are:
# "myaas.backends.mysql"
# "myaas.backends.postgres"
BACKEND = config("MYAAS_BACKEND", default="myaas.backends.mysql")


# Controls the debug mode of the application
DEBUG = config('MYAAS_DEBUG', default=False, cast=bool)

# Docker socket address, can be replaced with a TCP address iy you prefer not
# to bind mount the docker socket
DOCKER_HOST = config('MYAAS_DOCKER_HOST',
                     default=config('DOCKER_HOST',
                                    default="unix://var/run/docker.sock"))

# All containers created by this service will have this prefix in their name
CONTAINER_PREFIX = config('MYAAS_PREFIX', default='myaas-')
# Default time that a container stays up, in seconds.
CONTAINER_TTL = config('MYAAS_CONTAINER_TTL', cast=int, default=60*60*24)

# Default docker imgage for the mysql backend
# Currently tested with:
#  - mariadb:10
#  - mysql:5
#  - habitissimo/myaas-mysql:10.1 (based on mariadb:10)
MYSQL_IMAGE = config("MYAAS_MYSQL_IMAGE", default="habitissimo/myaas-mysql:10.1.23")
POSTGRES_IMAGE = config("MYAAS_POSTGRES_IMAGE", default="postgres:9.4")

DB_DATABASE = config("MYAAS_DB_DATABASE", default='default')
DB_USERNAME = config("MYAAS_DB_USERNAME", default='myaas')
DB_PASSWORD = config("MYAAS_DB_PASSWORD", default='myaas')

# Required environment variables for running the mysql image
# All of the listed images above need this environment variables

MYSQL_ENVIRONMENT = {
    #"MYSQL_RANDOM_ROOT_PASSWORD": "no",
    "MYSQL_ROOT_PASSWORD": DB_PASSWORD,
    "MYSQL_DATABASE": DB_DATABASE,
    "MYSQL_USER": DB_USERNAME,
    "MYSQL_PASSWORD": DB_PASSWORD,
}

POSTGRES_ENVIRONMENT = {
    "POSTGRES_DB": DB_DATABASE,
    "POSTGRES_USER": DB_USERNAME,
    "POSTGRES_PASSWORD": DB_PASSWORD,
}


# Memory limit to apply to every container (with docker syntax, eg: `2g`)
MEMORY_LIMIT = config('MYAAS_MEMORY_LIMIT', default='2g')
# How many CPUs to assign to every container
CPU_PINNING_INSTANCE_CORES = config("MYAAS_CPU_PINNING_CORES", cast=int, default=2)

# Internal settings
HOSTNAME = config('MYAAS_HOSTNAME', default='localhost')
BASE_DIR = config('MYAAS_BASE_DIR', default='/myaas')

DATA_DIR = BASE_DIR + "/data"
DUMP_DIR = BASE_DIR + "/dumps"
