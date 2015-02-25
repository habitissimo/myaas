from flask import Flask, Response, request, jsonify, abort

# from . import settings
from .utils.database import (
    get_database,
    list_databases,
    list_database_templates,
    database_from_template)


app = Flask(__name__)


@app.route('/', methods=['get'])
def hello_world():
    return jsonify(
        status="Service is running",
        templates=list_database_templates(),
        databases=list_databases())


@app.route('/db', methods=['get'])
def show_databases():
    return jsonify(databases=list_databases())


@app.route('/templates', methods=['get'])
def show_templates():
    return jsonify(templates=list_database_templates())


@app.route('/db/<template>/<name>', methods=['get'])
def inspect_database(template, name):
    db = get_database(template, name)
    if not db:
        abort(404)

    if request.args.get('all'):
        return jsonify(container=db.inspect())

    return jsonify(
        database=db.database,
        host=db.external_ip,
        port=db.external_port,
        user=db.user,
        password=db.password,
        running=db.running())


@app.route('/db/<template>/<name>', methods=['post'])
def create_database(template, name):
    db = get_database(template, name)
    if db:
        response = Response(status=304)  # not modified
        del response.headers['content-type']
        return response

    db = database_from_template(template, name)
    if not db:
        abort(404)
    db.start()
    response = inspect_database(template, name)
    response.status_code = 201
    return response


@app.route('/db/<template>/<name>', methods=['delete'])
def remove_database(template, name):
    db = get_database(template, name)
    if not db:
        abort(404)
    db.purge()
    response = Response(status=204)
    del response.headers['content-type']
    return response


@app.errorhandler(404)
def page_not_found(e):
    response = jsonify(status="Not found")
    response.status_code = 404
    return response
