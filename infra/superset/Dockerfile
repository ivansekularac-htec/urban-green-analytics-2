FROM apache/superset:5.0.0

USER root

# Install utilities required during bootstrap
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        zip \
        unzip \
    && rm -rf /var/lib/apt/lists/*

# Install additional Python dependencies
COPY requirements.txt /requirements.txt

RUN . /app/.venv/bin/activate \
    && uv pip install --no-cache-dir -r /requirements.txt

# Superset configuration
COPY superset_config.py /app/superset_config.py

# Bootstrap scripts
COPY init-superset.sh /app/init-superset.sh
COPY bootstrap /app/bootstrap

# Superset exports
COPY exports/roles.json /app/roles.json
COPY exports/dashboards_export.zip /app/dashboards_export.zip

# Make bootstrap scripts executable
RUN chmod +x \
        /app/init-superset.sh \
        /app/bootstrap/*.sh

ENV SUPERSET_CONFIG_PATH=/app/superset_config.py

USER superset