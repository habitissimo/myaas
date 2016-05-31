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
 -v "/opt/hops/db:/hops/db" \
 -e "HOST_NAME=`hostname`" \
 -e "MYSQL_DOCKER_IMAGE=habitissimo/myaas-mysql:10.1" \
 --restart=always \
  habitissimo/myaas
```

The first time you lauch it it will have no databases or templates, to add some templates read the next section.

# Updating template databases

Run a cron to rsync mysqldump files to `/opt/hops/db/dumps`, your cron will execute on the host machine, so make sure to adapt the path as necesary, depending on the volume mapping you are using.

At the end of your script put this:
```
docker run -t --rm --name=myaas-update \
 -v "/var/run/docker.sock:/var/run/docker.sock" \
 -v "/opt/hops/db:/hops/db" \
 -e "MYSQL_DOCKER_IMAGE=habitissimo/myaas-mysql:10.1" \
 habitissimo/myaas update
```

While the base databases are being updated you can't interact with the service, that's why you should stop it before updating data.

# Volumes

`/hops/db/dumps`
  Contains the sqldumps to import when creating a new database. The file has to be named like {template_name}.sql

`/hops/db/data`
  Contains binary data for each database created.
  Base image for any template will be in `/hops/db/data/{template_name}`.
  Copies derived from in will be stored in `/hops/db/data/{template_name}-{instance_name}`.

# Environment variables

You can provide some configuration parameters trough environemnt variables.

 * **HOST_NAME**: The hostname the service should show as a connection endpoint for itself.
 
 * **MYSQL_DOCKER_IMAGE**: the mysql image used to spawn new databases.
    * Default value: habitissimo/myaas-mysql:10.1
    
 * **MYSQL_ROOT_PASSWORD**: the password to be set for root access in create databases.
    * Default value: jiberish
    
 * **MYSQL_DATABASE**: name of the database to create. (The name is the same always for all instances from all templates, yo will identify them by container name).
    * Default value: default
    
 * **HOPS_DATA_DIR**: Path where the application will store database instances.
    * Default value: `/opt/hops/db/data`
    
 * **HOPS_DUMP_DIR**: Path where the application will look for sql files to import.
    * Default value: `/opt/hops/db/dumps`
     
 * **HOPS_TEMP_DIR**: Path where the application will store temporary data.
    * Default value: `/opt/hops/db/tmp`

**Warning:** You can replace the `MYSQL_DOCKER_IMAGE` by a custom one, but the code makes some asumptions on how to launch the database image, `habitissimo/myaas-mysql` image requires the following environment variables to be passed to work: `MYSQL_ROOT_PASSWORD`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`.

Your image should be able to accept this environment variables (even if it will not use them) and shold not require aditional ones. The easiest way to customize the database settings is to create a derivate from habitissimo/myaas-mysql:10.1.
