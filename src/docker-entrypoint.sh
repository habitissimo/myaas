#!/bin/bash

case $1 in
  "update")
    python -m myaas.update
    exit 0
  ;;
esac

if [ -z $HOST_NAME ]; then
  >&2 echo ""
  >&2 echo "HOST_NAME environemnt variable is not set"
  exit 1
fi

exec "$@"
