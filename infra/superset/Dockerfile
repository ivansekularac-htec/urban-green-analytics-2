FROM apache/superset:5.0.0

USER root

COPY requirements.txt /tmp/requirements.txt

RUN . /app/.venv/bin/activate \
    && uv pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY superset_config.py /app/pythonpath/superset_config.py
COPY init/init-superset.sh /usr/local/bin/init-superset.sh

RUN chmod +x /usr/local/bin/init-superset.sh

USER superset

ENTRYPOINT ["/usr/local/bin/init-superset.sh"]
