FROM apache/superset:5.0.0

USER root

COPY requirements.txt /app/requirements-drivers.txt

RUN uv pip install \
    --no-cache-dir \
    -r /app/requirements-drivers.txt

COPY superset_config.py /app/pythonpath/superset_config.py

USER superset