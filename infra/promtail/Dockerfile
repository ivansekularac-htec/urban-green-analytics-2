# Promtail with the Urban Green config baked in, so the service ships its own
# config rather than depending on a bind-mount.
FROM grafana/promtail:3.2.1

# Destination keeps Promtail's default config path (-config.file default), so no
# command override is needed.
COPY promtail-config.yaml /etc/promtail/config.yml
