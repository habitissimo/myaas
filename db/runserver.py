from launcher.server import app
from launcher.settings import FLASK_DEBUG

app.debug = FLASK_DEBUG

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
