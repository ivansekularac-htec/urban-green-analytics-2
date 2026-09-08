# Prometheus with the Urban Green scrape config baked into the image, so the
# service ships its own prometheus.yml rather than depending on a bind-mount.
FROM prom/prometheus:v2.55.1

COPY prometheus.yml /etc/prometheus/prometheus.yml
