FROM ollama/ollama:latest

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY init-ollama.sh /usr/local/bin/init-ollama.sh

RUN chmod +x /usr/local/bin/init-ollama.sh