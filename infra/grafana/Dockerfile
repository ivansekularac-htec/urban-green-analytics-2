FROM grafana/grafana:13.2.1

# Baked in for a fresh checkout with no bind mount.
# docker-compose.yaml bind-mounts the same host paths 
# over these so local edits reload without a rebuild.
COPY provisioning /etc/grafana/provisioning
COPY dashboards /etc/grafana/dashboards
