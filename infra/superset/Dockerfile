FROM apache/superset:5.0.0

USER root

COPY requirements.txt /requirements.txt
COPY superset_config.py /app/superset_config.py
COPY init-superset.sh /app/init-superset.sh
COPY bootstrap /app/bootstrap
COPY exports /app/exports

ENV SUPERSET_CONFIG_PATH=/app/superset_config.py
ENV SUPERSET_DASHBOARD_BUNDLE=/app/exports/dashboards_export.zip
ENV PYTHONPATH=/app

RUN . /app/.venv/bin/activate \
    && uv pip install --no-cache-dir -r /requirements.txt \
    && chmod +x /app/init-superset.sh

USER superset
