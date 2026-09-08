FROM busybox:musl AS healthcheck

FROM grafana/loki:3.7.1

# grafana/loki has no shell and no wget/curl - copy in a single static
# binary just for the healthcheck. busybox's applets work when invoked as
# `busybox <applet> ...` directly, no symlinks or shell needed to dispatch.
COPY --from=healthcheck /bin/busybox /bin/busybox

COPY loki.yaml /etc/loki/local.yaml

CMD ["-config.file=/etc/loki/local.yaml", "-config.expand-env=true"]
