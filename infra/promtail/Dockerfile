# Promtail with the Urban Green config baked in, so the service ships its own
# config rather than depending on a bind-mount.
FROM grafana/promtail:3.2.1

COPY promtail-config.yaml /etc/promtail/config.yml

# Point at the config explicitly (self-documenting; survives a base-image
# default change). This is Promtail's default path, so the copy above satisfies it.
CMD ["-config.file=/etc/promtail/config.yml"]
