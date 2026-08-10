#!/bin/sh

set -eu

OLLAMA_HOST="${OLLAMA_HOST:-http://urbangreen-ollama:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:?OLLAMA_MODEL must be set}"

echo "Waiting for Ollama at ${OLLAMA_HOST}..."

until curl -fsS "${OLLAMA_HOST}/api/tags" >/dev/null; do
    sleep 2
done

echo "Ollama is ready."

echo "Checking whether model '${OLLAMA_MODEL}' is already cached..."

if curl -fsS "${OLLAMA_HOST}/api/tags" \
    | grep -Fq "\"name\":\"${OLLAMA_MODEL}\""; then
    echo "Model '${OLLAMA_MODEL}' is already cached."
    exit 0
fi

echo "Model '${OLLAMA_MODEL}' is not cached. Pulling..."

ollama pull "${OLLAMA_MODEL}"

echo "Model '${OLLAMA_MODEL}' is ready."