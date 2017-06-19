#!/bin/bash

case $1 in
  "update")
    python -m myaas.update
    exit 0
  ;;
  "reaper")
    python -m myaas.reaper
    exit 0
  ;;
esac

if [ -z $MYAAS_HOSTNAME ]; then
  >&2 echo ""
  >&2 echo "MYAAS_HOSTNAME environment variable is not set"
  exit 1
fi

exec "$@"
