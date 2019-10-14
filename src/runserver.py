from myaas.server import app
from myaas.settings import DEBUG, SENTRY_DSN

app.debug = DEBUG

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[FlaskIntegration()]
)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
