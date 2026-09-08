FROM grafana/loki:3.6.11

COPY --chown=10001:10001 loki.yaml /etc/loki/loki.yaml

CMD ["-config.file=/etc/loki/loki.yaml", "-target=all"]
