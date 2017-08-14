# Optimized MySQL image for running with myaas

Available on docker hub as `habitissimo/habitissimo/myaas-mysql`.

 * UTF-8 (unicode ci) by default
 * Small query cache
 * Small InnoDB pool (but bigger than default)
 * InnoDB optimized for SSD
 * No double write (no ACID guarantees)
 * No native AIO (causes problems on COW filesystems, at least on btrfs)
