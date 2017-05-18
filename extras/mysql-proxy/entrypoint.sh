#!/bin/bash
set -e

export MYAAS_WAIT_TIMEOUT=${MYAAS_WAIT_TIMEOUT:-15}
export MYAAS_DEBUG=${MYAAS_DEBUG:-0}
export MYAAS_NO_REMOVE=${MYAAS_NO_REMOVE:-0}
export CURL="curl --dump-header /tmp/headers.txt --fail -s"
export PID=0

print_ts()
{
  echo "$(date):  $1"
}

find_or_create_database()
{
  local ret=0
  print_ts "* Looking for existing database ${MYAAS_TEMPLATE}/${MYAAS_NAME} ..."
  JSON=`$CURL ${MYAAS_URL}/db/${MYAAS_TEMPLATE}/${MYAAS_NAME}` || ret=$?
  debug_last_request $ret
  if [ $ret -ne 0 ]; then
    print_ts "  - No existing database found"
    local n=0
    until [ $n -ge 5 ]
    do
      create_database && break
      print_ts "  - Failed database creation"
      n=$[$n+1]
      sleep 2
    done
  else
    print_ts "  - Database found"
  fi

  HOST=`echo $JSON | jq -M -r '.host'`
  PORT=`echo $JSON | jq -M -r '.port'`

  return 0
}

create_database()
{
  local ret=0
  print_ts "* Creating database"
  JSON=`$CURL -X POST ${MYAAS_URL}/db/${MYAAS_TEMPLATE}/${MYAAS_NAME}` || ret=$?
  debug_last_request $ret
  if [ -z "$JSON" ]; then
    print_ts "  - [ERROR] Empty server response"
    return 1
  fi

  return 0
}


remove_database()
{
  local ret=0

  if [ $MYAAS_NO_REMOVE -ne 0 ]; then
    return
  fi

  print_ts "* Removing database..."
  JSON=`$CURL -X DELETE ${MYAAS_URL}/db/${MYAAS_TEMPLATE}/${MYAAS_NAME}` || ret=$?
  debug_last_request $ret
  if [ $ret -eq 0 ]; then
      print_ts "  - Deleted ${MYAAS_TEMPLATE}-${MYAAS_NAME}"
  else
      print_ts "  - Not found ${MYAAS_TEMPLATE}-${MYAAS_NAME}"
  fi
}

proxy_start()
{
  print_ts "* Starting proxy..."
  socat TCP-LISTEN:3306,reuseaddr,retry=5,fork TCP:$HOST:$PORT &
  PID=$!
  print_ts "  - Done"
  wait $PID
}

wait_database()
{
  local WAITED=0
  echo -n "$(date):  * waiting for TCP connections to $HOST:$PORT ..."
  while ! nc -w 1 -z $HOST $PORT 2>/dev/null
  do
    if [ $WAITED -ge $MYAAS_WAIT_TIMEOUT ]; then
      echo ""
      print_ts " - wait timeout reached"
      return 1
    fi
    echo -n .
    sleep 1
    WAITED=$((WAITED + 1))
  done
  echo "OK"
  print_ts " - connection stablished"

  return 0
}

debug_last_request()
{
  local exit_status=$1

  if [ $MYAAS_DEBUG -ne 0 ]; then
    print_ts "----------- LAST REQUEST: -----------"
    echo "Exit status was: $exit_status"
    if [ $exit_status -ne 0 ]; then
      echo "Refer to https://curl.haxx.se/libcurl/c/libcurl-errors.html to find error code meaning"
    fi
    echo ""
    cat /tmp/headers.txt
    echo $JSON | jq 2>/dev/null
    # if jq didn0t parse valid JSON print the raw contents
    if [ $? -ne 0 ]; then
      echo $JSON
    fi
    print_ts "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
  fi
}

# signal handler to remove database when the container is stopped
signal_handler()
{
    echo ""
    if [ $PID -ne 0 ]; then
      kill $PID || true
    fi
    remove_database
    exit 0
}


## MAIN ##

# Chek required config
for var in "MYAAS_URL" "MYAAS_TEMPLATE" "MYAAS_NAME"; do
  eval "value=\$$var"
  if [ -z $value ]; then
    print_ts "Missing required variable $var"
    exit 2
  fi
done

export CUR_RETRIES=0
export MAX_RETRIES=5

trap signal_handler SIGTERM SIGINT ERR

if [ $MYAAS_DEBUG -ne 0 ]; then
  print_ts "Debug is enabled"
fi

print_ts "Using server ${MYAAS_URL}"

find_or_create_database
until wait_database; do
  if [ $CUR_RETRIES -ge $MAX_RETRIES ]; then
    echo ""
    print_ts "Max retries reached, aborting..."
    remove_database
    exit 1
  fi
  find_or_create_database
  sleep 2
  CUR_RETRIES=$((CUR_RETRIES+1))
done
proxy_start # waits until proxy is killed
remove_database
