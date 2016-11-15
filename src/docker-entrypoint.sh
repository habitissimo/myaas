#!/bin/bash

case $1 in
  "update")
    python -m myaas.update
    exit 0
  ;;
  "daemon")
    python -m myaas.daemon
    exit 0
  ;;
esac

if [ -z $HOST_NAME ]; then
  >&2 echo ""
  >&2 echo "HOST_NAME environment variable is not set"
  exit 1
fi

exec "$@"
