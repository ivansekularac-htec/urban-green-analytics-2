FROM apache/superset:5.0.0

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt

COPY --chown=superset superset_config.py /app/
COPY --chown=superset docker-entrypoint.sh /app/

RUN chmod +x /app/docker-entrypoint.sh

ENV SUPERSET_CONFIG_PATH=/app/superset_config.py
