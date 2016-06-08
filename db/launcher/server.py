from flask import Flask, Response, request, jsonify, abort

from .utils.container import client
from .utils.database import get_myaas_containers
from .utils.database import list_databases, list_database_templates
from .backends.mysql import MysqlDatabase, MysqlDatabaseTemplate
from .backends.exceptions import (NonExistentDatabase, NonExistentTemplate,
                                  ImportInProgress)

app = Flask(__name__)


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
    try:
        db = MysqlDatabase(client, template, name)
    except NonExistentDatabase:
        abort(404)

    if request.args.get('all'):
        return jsonify(container=db.inspect())

    return jsonify(
        database=db.database,
        host=db.external_ip,
        port=db.external_port,
        user=db.user,
        password=db.password,
        running=db.running(),
        status=db.container['Status'],
        created=db.container['Created'])


@app.route('/db/<template>/<name>', methods=['post'])
def create_database(template, name):
    try:
        db = MysqlDatabase(client, template, name)
        response = Response(status=304)  # not modified
        del response.headers['content-type']
        return response
    except NonExistentDatabase:
        pass

    try:
        template_db = MysqlDatabaseTemplate(client, template)
        db = template_db.clone(name)
        db.start()
    except ImportInProgress:
        response = jsonify(status="Database not available, content is being imported.")
        response.status_code = 500
        return response
    except NonExistentTemplate:
        response = jsonify(status="Template \"{0}\" does not exists.".format(template))
        response.status_code = 500
        return response

    response = inspect_database(template, name)
    response.status_code = 201
    return response


@app.route('/db/<template>/<name>', methods=['delete'])
def remove_database(template, name):
    try:
        db = MysqlDatabase(client, template, name)
        db.purge()
    except NonExistentDatabase:
        abort(404)

    response = Response(status=204)
    del response.headers['content-type']
    return response


@app.errorhandler(404)
def page_not_found(e):
    response = jsonify(status="Not found")
    response.status_code = 404
    return response
