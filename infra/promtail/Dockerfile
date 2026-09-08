# 3.6.x is the last release line that still ships a promtail image - Loki
# 3.7.x removed Promtail from the build entirely (Promtail hit EOL 2026-03-02;
# all new development moved to Grafana Alloy). Loki itself is pinned newer
# since only Promtail's build was dropped, not compatibility with its clients.
FROM busybox:musl AS healthcheck

FROM grafana/promtail:3.6.8

# This image has a shell but no wget/curl - same fix as Loki's Dockerfile,
# for the same reason.
COPY --from=healthcheck /bin/busybox /bin/busybox

COPY promtail.yaml /etc/promtail/promtail.yml

CMD ["-config.file=/etc/promtail/promtail.yml", "-config.expand-env=true"]
