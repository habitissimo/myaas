import logging
import os

from flask import Flask, Response, request, jsonify, abort

from .settings import HOSTNAME, DEBUG
from .utils.container import client
from .utils.database import (get_myaas_containers, get_enabled_backend,
                             list_databases, list_database_templates)
from .backends.exceptions import (NonExistentDatabase, NonExistentTemplate,
                                  ImportInProgress)

app = Flask(__name__)

logger = logging
logger.basicConfig(
    format='%(asctime)s {:4} %(levelname)s: %(message)s'.format(os.getpid()),
    level=logging.DEBUG if DEBUG else logging.WARNING)

@app.route('/', methods=['get'])
def hello_world():
    return jsonify(
        status="Service is running",
        templates=list_database_templates(),
        databases=list_databases())


@app.route('/db', methods=['get'])
def show_databases():
    databases = []
    for c in get_myaas_containers():
        databases.append({
            'template': c['Labels']['com.myaas.template'],
            'name': c['Labels']['com.myaas.instance'],
            'state': c['Status'],
            'created': c['Created'],
        })

    return jsonify(databases=databases)


@app.route('/templates', methods=['get'])
def show_templates():
    return jsonify(templates=list_database_templates())


@app.route('/db/<template>/<name>', methods=['get'])
def inspect_database(template, name):
    logger.debug("requested inspect DB for: \"{template}\" => \"{name}\"".format(**locals()))
    database = get_enabled_backend().Database
    try:
        db = database(client, template, name)
    except NonExistentDatabase:
        logger.debug("database not found \"{template}\" => \"{name}\"".format(**locals()))
        abort(404)

    if request.args.get('all'):
        return jsonify(container=db.inspect())

    return jsonify(
        database=db.database,
        host=HOSTNAME,
        port=db.host_port,
        user=db.user,
        password=db.password,
        running=db.running(),
        status=db.container['Status'],
        created=db.container['Created'])


@app.route('/db/<template>/<name>', methods=['post'])
def create_database(template, name):
    logger.debug("requested create DB from \"{template}\" as \"{name}\"".format(**locals()))
    database_class = get_enabled_backend().Database
    try:
        db = database_class(client, template, name)
        logger.warning("already exists \"{template}\" as \"{name}\"".format(**locals()))
        response = Response(status=304)  # not modified
        del response.headers['content-type']
        return response
    except NonExistentDatabase:
        pass

    template_class = get_enabled_backend().Template
    try:
        template_db = template_class(client, template)
        logger.debug("found template \"{template}\"".format(**locals()))
        db = template_db.clone(name)
        logger.debug("starting database \"{template}\" => \"{name}\"".format(**locals()))
        db.start()
    except ImportInProgress:
        logger.error("requested template \"{template}\" not available, import in progress".format(**locals()))
        response = jsonify(status="Database not available, content is being imported.")
        response.status_code = 500
        return response
    except NonExistentTemplate:
        logger.error("requested template \"{template}\" not found".format(**locals()))
        response = jsonify(status="Template \"{0}\" does not exists.".format(template))
        response.status_code = 500
        return response

    response = inspect_database(template, name)
    response.status_code = 201
    return response


@app.route('/db/<template>/<name>', methods=['delete'])
def remove_database(template, name):
    logger.debug("requested delete DB \"{template}\" => \"{name}\"".format(**locals()))
    database_class = get_enabled_backend().Database
    try:
        db = database_class(client, template, name)
        db.remove()
        logger.debug("removed")
    except NonExistentDatabase:
        logger.debug("database not found \"{template}\" => \"{name}\"".format(**locals()))
        abort(404)

    response = Response(status=204)
    del response.headers['content-type']
    return response


@app.errorhandler(404)
def page_not_found(e):
    response = jsonify(status="Not found")
    response.status_code = 404
    return response
