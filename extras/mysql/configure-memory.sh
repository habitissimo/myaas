#!/bin/bash

# get max available memory from inside container
HARD_LIMIT_IN_BYTES=$(cgget -n  --values-only --variable memory.limit_in_bytes /)
HARD_LIMIT_IN_MEGABYTES=$(echo "${HARD_LIMIT_IN_BYTES}/1024/1024" | bc)
SOFT_LIMIT_IN_BYTES=$(cgget -n  --values-only --variable memory.soft_limit_in_bytes /)
SOFT_LIMIT_IN_MEGABYTES=$(echo "${SOFT_LIMIT_IN_BYTES}/1024/1024" | bc)

# get lower limit as effective limit
if [[ $HARD_LIMIT_IN_MEGABYTES -le $SOFT_LIMIT_IN_MEGABYTES ]]; then
  LIMIT_IN_MEGABYTES=$HARD_LIMIT_IN_MEGABYTES
else
  LIMIT_IN_MEGABYTES=$SOFT_LIMIT_IN_MEGABYTES
fi

# If reserved memory is more than 2GB
if [[ "$LIMIT_IN_MEGABYTES" -gt "2048"  ]]; then
  # Use all but 1GB for InnoDB
  POOL_SIZE=$(echo "${LIMIT_IN_MEGABYTES} - 1024" | bc)
  # Create n pool instance of at least 1Gb each
  POOL_INSTANCES=$(echo "$POOL_SIZE/1024" | bc)
else
  # use a 50% memory for Innodb
  POOL_SIZE=$(echo "${LIMIT_IN_MEGABYTES} / 2" | bc)
  POOL_INSTANCES=1
fi

echo ""
echo "Configuring InnoDB instance pool"
echo "HARD MEMORY LIMIT: ${HARD_LIMIT_IN_MEGABYTES}M"
echo "SOFT MEMORY LIMIT: ${SOFT_LIMIT_IN_MEGABYTES}M"
echo "POOL_SIZE: ${POOL_SIZE}M"
echo "POOL_INSTANCES: ${POOL_INSTANCES}"
echo ""

sed -i "s/^innodb_buffer_pool_size.*/innodb_buffer_pool_size = ${POOL_SIZE}M/" /etc/mysql/conf.d/myaas.cnf
sed -i "s/^innodb_buffer_pool_instances.*/innodb_buffer_pool_instances = ${POOL_INSTANCES}/" /etc/mysql/conf.d/myaas.cnf
