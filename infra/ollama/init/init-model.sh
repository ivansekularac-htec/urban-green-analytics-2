#!/bin/sh
set -eu

# Pull the configured Ollama model.
# Safe to re-run: Ollama skips the download when the model is already cached.
# Starts only after urbangreen-ollama is healthy (compose depends_on).

echo "Pulling Ollama model '${OLLAMA_MODEL}'..."
ollama pull "${OLLAMA_MODEL}"

echo "Ollama model '${OLLAMA_MODEL}' is ready."