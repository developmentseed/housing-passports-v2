# Postgres configuration

This short documentation for improving the DB performance in HP transactions.

Refs:

- https://www.postgresql.org/docs/11/runtime-config-resource.html
- https://wiki.postgresql.org/wiki/Tuning_Your_PostgreSQL_Server

# Available configuration

make sure your docker resource configuration has available resources to support it.

- xlarge: CPU 4 and RAM 8GB
- 4xlarge: CPU 16 and RAM 32GB

For selecting the configuration for machine type you should be set on the `docker-compose.yaml` file

- SET_SERVER_CONFING: true
- MACHINE_TYPE: xlarge