from myaas.server import app
from myaas.settings import DEBUG

app.debug = DEBUG

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
