#!/bin/sh
set -e

if [ "$SET_SERVER_CONFING" = "true" ]; then 

    # Configuration for a machine 8GB RAM and 4 CPU
    if [ "$MACHINE_TYPE" = "xlarge" ]; then 
        shared_buffers=3GB
        effective_cache_size=9GB
        maintenance_work_mem=768MB
        checkpoint_completion_target=0.7
        wal_buffers=16MB
        default_statistics_target=100
        random_page_cost=1.1
        effective_io_concurrency=200
        work_mem=78643kB
        min_wal_size=1GB
        max_wal_size=4GB
        max_worker_processes=4
        max_parallel_workers_per_gather=2
        max_parallel_workers=4
        max_parallel_maintenance_workers=2
    fi
    # Configuration for a machine 32GB RAM and 16 CPU
    if [ "$MACHINE_TYPE" = "4xlarge" ]; then 
        shared_buffers=8GB
        effective_cache_size=24GB
        maintenance_work_mem=2GB
        checkpoint_completion_target=0.9
        wal_buffers=16MB
        default_statistics_target=500
        random_page_cost=1.1
        effective_io_concurrency=200
        work_mem=26214kB
        min_wal_size=4GB
        max_wal_size=16GB
        max_worker_processes=16
        max_parallel_workers_per_gather=8
        max_parallel_workers=16
        max_parallel_maintenance_workers=4
    fi

    # Configuration 16.0 GiB	8 vCPUs	
    if [ "$MACHINE_TYPE" = "2xlarge" ]; then 
        shared_buffers=6GB
        effective_cache_size=14GB
        maintenance_work_mem=1536MB
        checkpoint_completion_target=0.7
        wal_buffers=32MB
        default_statistics_target=100
        random_page_cost=1.1
        effective_io_concurrency=400
        work_mem=157286kB
        min_wal_size=2GB
        max_wal_size=8GB
        max_worker_processes=8
        max_parallel_workers_per_gather=4
        max_parallel_workers=8
        max_parallel_maintenance_workers=4
    fi

    echo "Set configuration for db $MACHINE_TYPE server..."
    echo "shared_buffers = $shared_buffers"
    echo "effective_cache_size = $effective_cache_size"
    echo "maintenance_work_mem = $maintenance_work_mem"
    echo "checkpoint_completion_target = $checkpoint_completion_target"
    echo "wal_buffers = $wal_buffers"
    echo "default_statistics_target = $default_statistics_target"
    echo "random_page_cost = $random_page_cost"
    echo "effective_io_concurrency = $effective_io_concurrency"
    echo "work_mem = $work_mem"
    echo "min_wal_size = $min_wal_size"
    echo "max_wal_size = $max_wal_size"
    echo "max_worker_processes = $max_worker_processes"
    echo "max_parallel_workers_per_gather = $max_parallel_workers_per_gather"
    echo "max_parallel_workers = $max_parallel_workers"
    echo "max_parallel_maintenance_workers = $max_parallel_maintenance_workers"
    sed -i -e 's/shared_buffers = 128MB/shared_buffers = '$shared_buffers'/g' $PGDATA/postgresql.conf
    sed -i -e 's/#effective_cache_size = 4GB/effective_cache_size = '$effective_cache_size'/g' $PGDATA/postgresql.conf
    sed -i -e 's/#maintenance_work_mem = 64MB/maintenance_work_mem = '$maintenance_work_mem'/g' $PGDATA/postgresql.conf
    sed -i -e 's/#checkpoint_completion_target = 0.5/checkpoint_completion_target = '$checkpoint_completion_target'/g' $PGDATA/postgresql.conf
    sed -i -e 's/#wal_buffers = -1/wal_buffers = '$wal_buffers'/g' $PGDATA/postgresql.conf
    sed -i -e 's/#default_statistics_target = 100/default_statistics_target = '$default_statistics_target'/g' $PGDATA/postgresql.conf
    sed -i -e 's/#random_page_cost = 4.0/random_page_cost = '$random_page_cost'/g' $PGDATA/postgresql.conf
    sed -i -e 's/#effective_io_concurrency = 1/effective_io_concurrency = '$effective_io_concurrency'/g' $PGDATA/postgresql.conf
    sed -i -e 's/#work_mem = 4MB/work_mem = '$work_mem'/g' $PGDATA/postgresql.conf
    sed -i -e 's/max_wal_size = 1GB/max_wal_size = '$max_wal_size'/g' $PGDATA/postgresql.conf
    sed -i -e 's/min_wal_size = 80MB/min_wal_size = '$min_wal_size'/g' $PGDATA/postgresql.conf
    sed -i -e 's/#max_worker_processes = 8/max_worker_processes = '$max_worker_processes'/g' $PGDATA/postgresql.conf
    sed -i -e 's/#max_parallel_workers_per_gather = 2/max_parallel_workers_per_gather = '$max_parallel_workers_per_gather'/g' $PGDATA/postgresql.conf
    sed -i -e 's/#max_parallel_workers = 8/max_parallel_workers = '$max_parallel_workers'/g' $PGDATA/postgresql.conf
    sed -i -e 's/#max_parallel_maintenance_workers = 2/max_parallel_maintenance_workers = '$max_parallel_maintenance_workers'/g' $PGDATA/postgresql.conf
fi

