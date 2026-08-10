#!/bin/sh
# Prepare the configured Ollama model for the Module 5 reporting automation.
# Runs inside the one-shot urbangreen-ollama-init container.
#
# Two steps, both idempotent - re-running this container is a no-op:
#   1. Pull the base model, skipped when it is already in the cache volume so a
#      normal restart does not re-download.
#   2. Derive the served model with generation bounded by a Modelfile. This is
#      what keeps an automated call from hanging: qwen3.5 is a thinking model,
#      so it streams a reasoning block before answering. num_predict caps the
#      response and the /no_think directive turns the reasoning off.
set -eu

BASE_MODEL="${OLLAMA_MODEL:-qwen3.5:2b}"
SERVED_MODEL="${OLLAMA_SERVED_MODEL:-urbangreen-report}"
NUM_PREDICT="${OLLAMA_NUM_PREDICT:-512}"
NUM_CTX="${OLLAMA_CONTEXT_LENGTH:-8192}"

echo "Base model:   ${BASE_MODEL}"
echo "Served model: ${SERVED_MODEL}"
echo "Bounds:       num_predict=${NUM_PREDICT} num_ctx=${NUM_CTX}"

if ollama show "${BASE_MODEL}" >/dev/null 2>&1; then
  echo "Ollama model '${BASE_MODEL}' is already cached."
else
  echo "Pulling Ollama model '${BASE_MODEL}'..."
  ollama pull "${BASE_MODEL}"
fi

# Rebuilt on every run: a thin manifest over the already-pulled weights, so it
# costs nothing and picks up changed bounds without a manual step.
MODELFILE="/tmp/${SERVED_MODEL}.Modelfile"

cat > "${MODELFILE}" <<EOF
FROM ${BASE_MODEL}

PARAMETER num_predict ${NUM_PREDICT}
PARAMETER num_ctx ${NUM_CTX}
PARAMETER temperature 0.3

SYSTEM """/no_think
You are a reporting assistant for the Urban Green Analytics platform.
Answer directly and concisely. Do not show reasoning steps.
"""
EOF

echo "Creating served model '${SERVED_MODEL}'..."
ollama create "${SERVED_MODEL}" -f "${MODELFILE}"

echo "Ollama model '${SERVED_MODEL}' is ready."
