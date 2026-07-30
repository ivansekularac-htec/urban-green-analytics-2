FROM apache/superset:5.0.0
 
USER root

# Install zip and unzip for password inject
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        zip \
        unzip \
    && rm -rf /var/lib/apt/lists/*
 
COPY requirements.txt /requirements.txt
COPY superset_config.py /app/superset_config.py
COPY init-superset.sh /app/init-superset.sh
COPY exports/roles.json /app/roles.json
COPY bootstrap_scripts/inject_db_password.sh /app/inject_db_password.sh
COPY exports/dashboards_export.zip /app/dashboards_export.zip
COPY bootstrap_scripts/create_users.sh /app/create_users.sh
COPY bootstrap_scripts/create_rls.py /app/create_rls.py

RUN chmod +x /app/inject_db_password.sh
RUN chmod +x /app/create_users.sh

ENV SUPERSET_CONFIG_PATH=/app/superset_config.py
 
RUN . /app/.venv/bin/activate \
    && uv pip install --no-cache-dir -r /requirements.txt \
    && chmod +x /app/init-superset.sh

USER superset

