FROM apache/superset:5.0.0
 
USER root
 
COPY requirements.txt /requirements.txt
COPY superset_config.py /app/superset_config.py

COPY init/init-superset.sh /app/init-superset.sh
COPY init/seed_users_roles.py /scripts/seed_users_roles.py
COPY init/seed_dashboard_access.py /scripts/seed_dashboard_access.py
COPY init/seed_rls.py /scripts/seed_rls.py

ENV SUPERSET_CONFIG_PATH=/app/superset_config.py
 
RUN . /app/.venv/bin/activate \
    && uv pip install --no-cache-dir -r /requirements.txt \
    && chmod +x /app/init-superset.sh

USER superset

