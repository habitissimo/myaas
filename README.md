[![Docker Build Statu](https://img.shields.io/docker/build/habitissimo/myaas.svg)]()
[![Docker Pulls](https://img.shields.io/docker/pulls/habitissimo/myaas.svg)]()
[![Docker Automated buil](https://img.shields.io/docker/automated/habitissimo/myaas.svg)]()

# MyAAS (Mysql As A Service)

This product has been developed internally at habitissimo for allowing developers to get the database instances they need for development as fast as possible.

## What this project does

This project consists on a service which will import a collection of databases periodically. This databases become templates for the final users.

An user can ask for a database instance from any template available and have it fully functional and loaded with data within seconds, no matter how big is the database, this databases can be destroyed at any moment to request a new instance with fresh data.

## Speed

The main concern we where having in our development process was importing database backups in our development instances, loading this backups by tradicional means (importing a mysqldump file) could take almost an hour, we could use other metohds like innobackupex, but this would mean developers had to download huge files (even with compression) trading speed in import time by slownes in download time.

This solution is being used to provide a variety of databases ranging from a few megabytes up to several gigabytes, all of them are provisioned within seconds (something between 3 or 5 seconds).

## How it works

You put your sql backups in a folder and run the updater command, this will import the databases and prepare them as templates. This is the slow part, we run it at nights so developers can have acces to yesterday's data in the morning.

The backups are loaded into a dockerized mysql instance, this docker container binds the datadir to a host volume stored on a filesystem with [Copy On Write](https://es.wikipedia.org/wiki/Copy-on-write) support.

Once the templates have been loaded the script stops the template database instances.

Every time a user asks for a new database the service performs a copy on write from the template to a new directory, this directory is mounted as a volume
for a new mysql docker instance launched for this user. As the operation is performed against a [COW](https://es.wikipedia.org/wiki/Copy-on-write) filesystem the operation is both fast and space efficient.

Finally the service responds with access data required to use the database.

## What you will find here:

 - **src**: myaas source [read more](db/README.md)
 - **fabfile**: example client to interact with myaas [read more](fabfile/README.md)

## TODO
 - [ ] Use docker volume API instead of hacking arround with volume bindings
 - [ ] Create adapters for postgresql and mongodb
 - [ ] Update testsuite, broken after refactoring

## Extendibility

MyAAS has been designed with mysql in mind, but the implementation is database agnostic and can be adapted easily to work with any type of database which stores data in disk.

Look for [MysqlDatabase adapter](src/myaas/backends/mysql.py) to have an idea of how easy is to support new databases, you just need to extend [AbstractDatabase](src/myaas/backends/base.py) and define a few properties.
 
## Support

If you have problems using this service [open an issue](../../Habitissimo/myass/issues).
Jola.
