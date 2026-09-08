# Prometheus with the Urban Green scrape config baked into the image, so the
# service ships its own prometheus.yaml rather than depending on a bind-mount.
FROM prom/prometheus:v2.55.1

# Source is prometheus.yaml (repo convention); the destination keeps the image's
# default config path (/etc/prometheus/prometheus.yml) so no --config.file flag
# is needed.
COPY prometheus.yaml /etc/prometheus/prometheus.yml
