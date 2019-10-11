FROM python:3.6

RUN apt-get update -y && \
    apt-get install -y mysql-client postgresql-client btrfs-tools && \
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
ADD gunicorn.conf.py /code/


ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "runserver:app"]

HEALTHCHECK --interval=5s --timeout=2s --retries=3 CMD curl --fail http://127.0.0.1/ || exit 1
