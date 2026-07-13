FROM clickhouse/clickhouse-server:24.8

# The base image runs every *.sql / *.sh from here alphabetically on first start
# (only when the data dir is empty).
COPY sql/ /docker-entrypoint-initdb.d/
