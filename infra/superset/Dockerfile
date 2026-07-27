FROM apache/superset:5.0.0

USER root

COPY requirements.txt /requirements.txt
COPY superset_config.py /app/pythonpath/superset_config.py
COPY entrypoint.sh /entrypoint.sh

RUN . /app/.venv/bin/activate \
    && uv pip install --no-cache-dir -r /requirements.txt \
    && chmod +x /entrypoint.sh

USER superset

ENTRYPOINT ["/entrypoint.sh"]