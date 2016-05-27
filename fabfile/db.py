import requests
import pprint
import sys
try:
    from urllib.parse import urljoin
except:
    from urlparse import urljoin

from fabric.api import env
from taskset import TaskSet, task_method


class DBApiClient(object):

    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {'Accept': 'text/plain, application/json'}

    def get(self, url, expects=[200], **kwargs):
        return self._command('get', url, expects, **kwargs)

    def post(self, url, expects=[201,304], **kwargs):
        return self._command('post', url, expects, **kwargs)

    def delete(self, url, expects=[204,304], **kwargs):
        return self._command('delete', url, expects, **kwargs)

    def _command(self, verb, url, expects, **kwargs):
        try:
            response = requests.request(verb, urljoin(self.base_url, url),
                                        headers=self.headers, **kwargs)
        except requests.exceptions.ConnectionError:
            print("Could not connect to API endpoint, maybe the service is down")
            sys.exit(1)

        if response.status_code == 404:
            print("Database not found")
            sys.exit(1)

        if response.status_code not in expects:
            print("An error happened")
            try:
                pprint.pprint(response.json())
            except:
                pprint.pprint(response.request.headers)
                pprint.pprint(response.text)
            sys.exit(1)

        return response


class DBProvider(TaskSet):
    def __init__(self):
        self.client = DBApiClient(env.db_multiplexer_url)

    @task_method
    def new(self, template, name):
        response = self.client.post('/db/{template}/{name}'.format(**locals()))
        if response.status_code == 304:
            print("This database already exists")
            return
        pprint.pprint(response.json())

    @task_method
    def info(self, template, name):
        response = self.client.get('/db/{template}/{name}'.format(**locals()))
        pprint.pprint(response.json())

    @task_method
    def shell(self, template, name):
        response = self.client.get('/db/{template}/{name}'.format(**locals()))
        print("mysql -u{user} -p{password} --host={host} --port={port} {database}".format(**response.json()))
        sys.exit(1) # prevent fabric to add 'Done' at the end

    @task_method
    def rm(self, template, name):
        self.client.delete('/db/{template}/{name}'.format(**locals()))
        print("Database deleted")

    @task_method
    def ls(self):
        response = self.client.get('/db')
        pprint.pprint(response.json()[u'databases'])

    @task_method
    def templates(self):
        response = self.client.get('/templates')
        pprint.pprint(response.json()[u'templates'])

    @task_method
    def container(self, template, name):
        response = self.client.get('/db/{template}/{name}'.format(**locals()),
                                   params={'all': True})
        pprint.pprint(response.json())
