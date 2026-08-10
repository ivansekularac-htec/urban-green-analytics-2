#!/bin/sh
# Pull the configured Ollama model when it is not already cached.
# Runs inside the one-shot urbangreen-ollama-init container.
set -eu

OLLAMA_MODEL="${OLLAMA_MODEL:-qwen3.5:2b}"

if ollama show "${OLLAMA_MODEL}" >/dev/null 2>&1; then
  echo "Ollama model '${OLLAMA_MODEL}' is already cached."
else
  echo "Pulling Ollama model '${OLLAMA_MODEL}'..."
  ollama pull "${OLLAMA_MODEL}"
fi

echo "Ollama model '${OLLAMA_MODEL}' is ready."