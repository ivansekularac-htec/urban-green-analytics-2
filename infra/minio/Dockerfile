# Thin pass-through over the official MinIO image.
# No customization is layered today; this build context exists so future
# tweaks (TLS, plugins) can land here without touching docker-compose.
FROM minio/minio:latest

# S3 API (9000) + web console (9001). Documentation only; actual publishing
# is done via `ports:` in docker-compose.
EXPOSE 9000 9001

# Start the MinIO server: store objects under /data, serve the console on :9001.
CMD ["server", "/data", "--console-address", ":9001"]
