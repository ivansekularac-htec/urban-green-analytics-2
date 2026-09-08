# Loki with the Urban Green config baked in, so the service ships its own
# config rather than depending on a bind-mount.
FROM grafana/loki:3.2.1

COPY loki-config.yaml /etc/loki/local-config.yaml

# Point at the config explicitly (self-documenting; survives a base-image
# default change). This is Loki's default path, so the copy above satisfies it.
CMD ["-config.file=/etc/loki/local-config.yaml"]
