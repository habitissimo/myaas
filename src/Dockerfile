FROM python:3.6

RUN apt-get update -y && \
    apt-get install -y mysql-client postgresql-client && \
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
ADD myaas /code/myaas/
ADD docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ADD runserver.py /code/

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "runserver:app", "-b", "0.0.0.0:5001", "--log-file=-", "--log-level=info", "-w=5", "--timeout=900"]
