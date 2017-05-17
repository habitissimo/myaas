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
        db = {
            'template': c['Labels']['com.myaas.template'],
            'name': c['Labels']['com.myaas.instance'],
            'state': c['Status'],
            'created': c['Created'],
        }
        if 'com.myaas.expiresAt' in c['Labels']:
            db.update({'expires_at': c['Labels']['com.myaas.expiresAt']})
        databases.append(db)

    return jsonify(databases=databases)


@app.route('/templates', methods=['get'])
def show_templates():
    return jsonify(templates=list_database_templates())


@app.route('/db/<template>/<name>', methods=['get'])
def inspect_database(template, name):
    logger.debug(f'requested inspect DB for: "{template}" => "{name}"')
    database = get_enabled_backend().Database
    try:
        db = database(client, template, name)
    except NonExistentDatabase:
        logger.debug(f'database not found "{template}" => "{name}"')
        abort(404)

    if request.args.get('all'):
        return jsonify(container=db.inspect())

    result = dict(
        database=db.database,
        host=HOSTNAME,
        name=db.name,
        port=db.host_port,
        user=db.user,
        password=db.password,
        running=db.running(),
        status=db.container['Status'],
        created=db.container['Created'],
    )

    if 'com.myaas.expiresAt' in db.container['Labels']:
        result.update({'expires_at': db.container['Labels']['com.myaas.expiresAt']})

    return jsonify(result)


@app.route('/db/<template>/<name>', methods=['post'])
def create_database(template, name):
    logger.debug(f'requested create DB from "{template}" as "{name}"')
    form_ttl = request.form.get("ttl")
    json_ttl = request.get_json(silent=True).get("ttl")
    ttl = form_ttl or json_ttl
    if ttl:
        ttl = int(ttl)
    database_class = get_enabled_backend().Database
    try:
        db = database_class(client, template, name)
        logger.warning(f'already exists "{template}" as "{name}"')
        response = Response(status=304)  # not modified
        del response.headers['content-type']
        return response
    except NonExistentDatabase:
        pass

    template_class = get_enabled_backend().Template
    try:
        template_db = template_class(client, template)
        logger.debug(f'found template "{template}"')
        db = template_db.clone(name, ttl=ttl)
        logger.debug(f'starting database "{template}" => "{name}"')
        db.start()
    except ImportInProgress:
        logger.error(f'requested template "{template}" not available, import in progress')
        response = jsonify(status="Database not available, content is being imported.")
        response.status_code = 500
        return response
    except NonExistentTemplate:
        logger.error(f'requested template "{template}" not found')
        response = jsonify(status=f'Template "{template}" does not exist.')
        response.status_code = 500
        return response

    response = inspect_database(template, name)
    response.status_code = 201
    return response


@app.route('/db/<template>/<name>', methods=['delete'])
def remove_database(template, name):
    logger.debug(f'requested delete DB "{template}" => "{name}"')
    database_class = get_enabled_backend().Database
    try:
        db = database_class(client, template, name)
        db.remove()
        logger.debug("removed")
    except NonExistentDatabase:
        logger.debug(f'database not found "{template}" => "{name}"')
        abort(404)

    response = Response(status=204)
    del response.headers['content-type']
    return response


@app.errorhandler(404)
def page_not_found(e):
    response = jsonify(status="Not found")
    response.status_code = 404
    return response
