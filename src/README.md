# DB replicator

This application uses docker to allow quick creation of databases for development and testing. The only database supported right now is Mysql/MariaDB but it's designed to make it really easy to adapt to any kind of database.

The application listens for commands trough HTTP on port 5001, a cli client is provided as an example.

# How it works

There is the concept of templates and databases.

A template is a read only database used to create new copies, templates are automatically loaded from a folder containing sql files. The import process is meant to be run by cron (at night for example). Once the import has been completed the read only database is stopped and we can use it later to duplicate the datadir and launch a new instance which will use the duplicated datadir.

## Client

There is a fabric interface for this service, enter the `fabfile ` directory and run `fab -l` to get a list of available commands.

Maybe you will need to install some dependencies first, inside the `fabfile` directory run `pip install -r requirements.txt`.

# Setup

To setup this service you only need to pull the image and run it.

```
# pull the image you are going to use for launching databases
# (edit if you are using a custom image)
# this is neccesary to prevent the application from giving a timeout exception
# when verifying the DB is up and running as it does expect the image to be
# present in advance

docker pull habitissimo/myaas-mysql:10.1

# create the multiplexer instance

docker run -d --name=myaas \
 -p 5001:5001 \
 -v "/var/run/docker.sock:/var/run/docker.sock" \
 -v "/opt/myaas:/myaas" \
 -e "HOST_NAME=`hostname`" \
 -e "MYSQL_DOCKER_IMAGE=habitissimo/myaas-mysql:10.1" \
 --restart=always \
  habitissimo/myaas
```

The first time you launch it it will have no databases or templates, to add some templates read the next section.

# Updating template databases

Run a cron to rsync mysqldump files to `/opt/myaas/dumps`, your cron will execute on the host machine, so make sure to adapt the path as necesary, depending on the volume mapping you are using.

At the end of your script put this:
```
docker run -t --rm --name=myaas-update \
 -v "/var/run/docker.sock:/var/run/docker.sock" \
 -v "/opt/myaas:/myaas" \
 -e "MYSQL_DOCKER_IMAGE=habitissimo/myaas-mysql:10.1" \
 habitissimo/myaas update
```

While the base databases are being updated you can't interact with the service, that's why you should stop it before updating data.

# Volumes

`/myaas/dumps`
  Contains the sqldumps to import when creating a new database. The file has to be named like {template_name}.sql

`/myaas/data`
  Contains binary data for each database created.
  Base image for any template will be in `/myaas/data/{template_name}`.
  Copies derived from in will be stored in `/myaas/data/{template_name}-{instance_name}`.

# Environment variables

You can provide some configuration parameters trough environemnt variables.

## Required

 * **MYAAS_HOST_NAME**: The hostname the service should show as a connection endpoint for itself (hostname or ip from the docker host).

## Performance
 * **MYAAS_MEMORY_LIMIT**: memory limit for each container created by myaas (using docker syntax).
    * Default value: `2g`

 * **MYAAS_CPU_PINNING_CORES**: Pin every container this number of CPUS. (InnoDB doesn't handle very well having more than 8 cores available, when used on a system with many cores this increases performance).
   * Defautl value: `2` (0 to disable)

## Optional

 * **MYAAS_DEBUG**: print debug logs to stdout.
    * Default value: `False`

 * **MYAAS_PREFIX**: prefix added to every container created by myaas.
   * Default value: `myaas`

 * **MYAAS_DOCKER_HOST**: Docker host to use.
   * Default value: `unix://var/run/docker.sock`

 * **MYAAS_CONTAINER_TTL**: Default TTL (in seconds) given to a new instance, if `reaper` process is running instances will be deleted after this time, used for autocleaning.
   * Default value: `0` (disabled)

 * **MYAAS_MYSQL_IMAGE**: the mysql image used to spawn new databases.
   * Default value: `habitissimo/myaas-mysql`

 * **MYAAS_DB_USERNAME**: the password to be set for root access in create databases.
   * Default value: `myaas`

 * **MYAAS_DB_PASSWORD**: the password to be set for root access in create databases.
   * Default value: `myaas`

 * **MYAAS_DB_DATABASE**: name of the database to create. (The database name is the same for all instances).
   * Default value: `myaas`

## Experimental

 * **MYAAS_BACKEND**: to switch between mysql and postgres.
   * Default value: `myaas.backends.mysql`
   * Available values: `myaas.backends.mysql` and `myaas.backends.postgres`

 * **MYAAS_POSTGRES_IMAGE**: the postgres image used to spawn new databases when backend is set to `myaas.backends.postgres`.
   * Default value: `postgres:9.4`


**Warning:** You can replace the `MYAAS_MYSQL_IMAGE` by a custom one, but it must be derived from `mariadb:10` or be compatible with it. Look at `settings.py` to see the environments passed to every new mysql container in the setting `MYSQL_ENVIRONMENT`.

The same goes for replacig `MYAAS_POSTGRES_IMAGE`, it must be derived from `postgres:9` or be compatible with it.

Your image should be able to accept this environment variables (even if it will not use them) and should not require aditional ones. The easiest way to customize the database settings is to create a derivate from habitissimo/myaas-mysql:10.1.
