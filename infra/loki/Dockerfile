FROM grafana/loki:3.6.11

COPY --chown=10001:10001 loki-config.yml /etc/loki/loki-config.yml

CMD ["-config.file=/etc/loki/loki-config.yml", "-target=all"]
