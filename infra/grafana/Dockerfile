# Grafana with datasource + dashboard provisioning baked in, so both datasources
# are connected on first boot. Compose also bind-mounts these same paths so JSON
# and provisioning edits reload without a rebuild.
FROM grafana/grafana:11.3.0

COPY provisioning /etc/grafana/provisioning
COPY dashboards /etc/grafana/dashboards
