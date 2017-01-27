FROM node:7

WORKDIR /code

COPY bower.json .

RUN npm install bower && \
    /code/node_modules/bower/bin/bower --allow-root install && \
    rm -rf node_modules

COPY . /code

ENTRYPOINT python -m SimpleHTTPServer 80
