FROM mdillon/postgis
# RUN apt-get update

RUN mkdir -p /docker-entrypoint-initdb.d
COPY ./config/server_config.sh /docker-entrypoint-initdb.d/