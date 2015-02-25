FROM python:3

RUN apt-get update -y && \
    apt-get install -y mysql-client && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /code/

# improve cacheability by copying first only the requirements
# files and installing dependencies
ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD requirements-dev.txt /code/
RUN pip install -r requirements-dev.txt

# copy all the rest
ADD launcher /code/launcher/
ADD tests /code/tests/
ADD docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ADD runserver.py /code/

ENV MYSQL_DOCKER_IMAGE library/mariadb:latest
ENV MYSQL_ROOT_PASSWORD jiberish
ENV MYSQL_DATABASE default
ENV DOCKER_SOCKET unix://var/run/docker.sock

# paths in host!
ENV HOPS_DATA_DIR /opt/hops/db/data
ENV HOPS_DUMP_DIR /opt/hops/db/dumps
ENV HOPS_TEMP_DIR /opt/hops/db/tmp

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "runserver:app", "-b", "0.0.0.0:5001", "--log-file=-", "--log-level=info", "-w=5", "--timeout=900"]
