# Mysql proxy for MyAAS

Available on docker hub as `habitissimo/mysql-proxy`.

You can use this image to integrate myaas in your docker workflow, any container linking to a mysql container can link to this image instead and use the myaas service transparently.

Despite the name indicates it is a proxy for mysql it should work for MyAAS working with any backend (including Postgres), but the listen port for the proxy is hardcoded to 3306. The proxy is protocol agnostic, it's just a TCP proxy.

## How it works

On start it will request a new database instance to the MyAAS server, once the instance is online it will run a socat proxy to it, your containers linking to this container will be able to connect to that mysql instance on port 3306. 

When the container is stoped it will send a request to the MyAAS server to delete the database (unless MYAAS_NO_REMOVE is set to a non 0 value).

## Usage

Example usage:

```
docker run -it \
    -e MYAAS_URL=http://myaas-server:5001 \
    -e MYAAS_TEMPLATE=template \
    -e MYAAS_NAME=name \
    habitissimo/mysql-proxy
```

## Environment variables

Required:
* **MYAAS_URL**: API endpoint of myaas instance
* **MYAAS_TEMPLATE**: template name to use for new database
* **MYAAS_NAME**: a name for the instance to be created

Optional:
* **MYAAS_NO_REMOVE**: (default is 0) do not remove created database on stop
* **MYAAS_WAIT_TIMEOUT**: (default is 15) max wait time in seconds until server is alive
* **MYAAS_DEBUG**: (default is 0) set to 1 to print debug information about curl requests
