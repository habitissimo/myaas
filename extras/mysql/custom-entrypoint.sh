#!/bin/bash

# original entrypoint skips running custom scripts if datadir exists
# but we want to execute this script every time the container is started
. /docker-entrypoint-initdb.d/configure-memory.sh

# now execute original entrypoint as ususal
. docker-entrypoint.sh "$@"
