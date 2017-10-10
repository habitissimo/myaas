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

## Quickstart

You could find more info at dockerhub [image documentation](https://hub.docker.com/r/habitissimo/myaas/).

The project needs a datadir over a [btrfs](https://en.wikipedia.org/wiki/Btrfs) filesystem. In this case we will create it at `/srv/myaas`.

In this directory two btrfs subvolumes are expected to exist:
    - `dumps`, where myaas will look for the sql backups to be converted into templates, and
    - `data`, where the templates datadirs will be copied for each myaas instance

```bash
 $ export BASE_DIR=/srv/myaas
 $ mkdir $BASE_DIR

 $ btrfs subvolume create $BASE_DIR/dumps
 $ btrfs subvolume create $BASE_DIR/data
```

Now we can put some sql backup in the `dumps` dir.

```bash
 $ echo "create table test (id int, name varchar(32));" >> $BASE_DIR/dumps/test_db.sql
 $ echo "insert into test values (1, 'alice'); insert into test values (2, 'bob');" >> $BASE_DIR/dumps/test_db.sql
```

Pull the docker image to be used as base, and run the updater to create a base template from the sql file.

```
 $ docker pull mariadb:10
 $ docker run --rm --name=myaas-updater \
  -v "/var/run/docker.sock:/var/run/docker.sock" \
  -v "/srv/myaas:/myaas" \
  -e "MYAAS_DB_DATABASE=default" \
  -e "MYAAS_DB_USERNAME=root" \
  -e "MYAAS_DB_PASSWORD=secret" \
  -e "MYAAS_MYSQL_IMAGE=mariadb:10" \
  --privileged \
  --no-healthcheck \
  habitissimo/myaas:devel update

- Creating database test_db
  * Starting database...
  * Started
  * Waiting for database to accept connections
  * Importing data...
  * Stopping database...
  * Stopped
```

Congrats, you have create your first database template! Now you can expose to your development team via a simple API:

```
 $ docker run --name myaas -d \
  --restart=on-failure:10 \
  -v "/var/run/docker.sock:/var/run/docker.sock" \
  -v "/srv/myaas:/myaas" \
  -p 5001:80 \
  -e "MYAAS_MYSQL_IMAGE=mariadb:10" \
  -e "MYAAS_HOSTNAME=localhost" \
  -e "MYAAS_DB_DATABASE=default" \
  -e "MYAAS_DB_USERNAME=root" \
  -e "MYAAS_DB_PASSWORD=secret" \
  --privileged \
  habitissimo/myaas
```

An example using [httpie](https://httpie.org/) to interact with the API, and the mysql client to connect to a recently created db instance:

```
 $ http --body localhost:5001/templates
{
    "templates": [
        "test_db"
    ]
}

 $ http POST localhost:5001/db/test_db/newdb ttl:=3600
HTTP/1.1 201 CREATED
Connection: close
Content-Length: 248
Content-Type: application/json
Date: Tue, 10 Oct 2017 08:24:17 GMT
Server: gunicorn/19.3.0

{
    "created": 1507623857,
    "database": "default",
    "expires_at": "1507627457.012895",
    "host": "localhost",
    "name": "newdb",
    "password": "secret",
    "port": "47327",
    "running": true,
    "status": "Up Less than a second",
    "user": "root"
}

 $ mysql -uroot -psecret --host=0.0.0.0 --port=47327 default
MariaDB [default]> select * from test;
+------+-------+
| id   | name  |
+------+-------+
|    1 | alice |
|    2 | bob   |
+------+-------+
2 rows in set (0.00 sec)
```

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
