from myaas.server import app
from myaas.settings import DEBUG, SENTRY_DSN

app.debug = DEBUG

if SENTRY_DSN:
    from raven.contrib.flask import Sentry
    Sentry(app, dsn=SENTRY_DSN)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
