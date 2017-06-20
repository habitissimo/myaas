#!/bin/bash

# get max available memory from inside container
LIMIT_IN_BYTES=$(cgget -n  --values-only --variable memory.limit_in_bytes /)
SOFT_LIMIT_IN_BYTES=$(cgget -n  --values-only --variable memory.soft_limit_in_bytes /)

if [ "$LIMIT_IN_BYTES" == "$SOFT_LIMIT_IN_BYTES" ]; then
  # Do nothing, memory not limited
  echo "Memory not limited, not changing innodb config"
  return
fi

# get 90% memory and convert it to megabytes
POOL_SIZE=$(echo "${LIMIT_IN_BYTES}*0.9/1024/1024" | bc)
POOL_INSTANCES=$(echo "$POOL_SIZE/1024" | bc)


echo ""
echo "Configuring InnoDB instance pool"
echo "POOL_SIZE: ${POOL_SIZE}M"
echo "POOL_INSTANCES: ${POOL_INSTANCES}"
echo ""

sed -i "s/^innodb_buffer_pool_size.*/innodb_buffer_pool_size = ${POOL_SIZE}M/" /etc/mysql/conf.d/myaas.cnf
sed -i "s/^innodb_buffer_pool_instances.*/innodb_buffer_pool_instances = ${POOL_INSTANCES}/" /etc/mysql/conf.d/myaas.cnf
