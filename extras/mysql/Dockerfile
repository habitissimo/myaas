FROM mariadb:10.1.23
MAINTAINER Hugo Chinchilla <hchinchilla@habitissimo.com>

# customize base config
ADD mariadb.cnf /etc/mysql/conf.d/mariadb.cnf
ADD myass.cnf /etc/mysql/conf.d/myass.cnf


CMD ["mysqld", "--innodb-doublewrite=0"]
