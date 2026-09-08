# Loki with the Urban Green config baked in, so the service ships its own
# config rather than depending on a bind-mount.
FROM grafana/loki:3.2.1

# Destination keeps Loki's default config path (-config.file default), so no
# command override is needed.
COPY loki-config.yaml /etc/loki/local-config.yaml
