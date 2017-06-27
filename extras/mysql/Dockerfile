FROM mariadb:10.1.23
MAINTAINER Hugo Chinchilla <hchinchilla@habitissimo.com>

# Install cgget command
RUN apt-get update && apt-get install -y cgroup-bin bc && rm -rf /var/apt/lists/* && apt-get clean

# customize base config
ADD mariadb.cnf /etc/mysql/conf.d/mariadb.cnf
ADD myaas.cnf /etc/mysql/conf.d/myaas.cnf

# make myaas.cnf writable
RUN chown -R mysql:mysql /etc/mysql/conf.d
ADD configure-memory.sh /docker-entrypoint-initdb.d/

# customize entrypoint
COPY custom-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["custom-entrypoint.sh"]

CMD ["mysqld", "--innodb-doublewrite=0"]

HEALTHCHECK --interval=5s --timeout=10s --retries=3 CMD mysql --user=root --password=$MYSQL_ROOT_PASSWORD -h 127.0.0.1 -e "show databases;"
