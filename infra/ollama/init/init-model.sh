#!/bin/sh
# Prepare the configured Ollama model for the reporting automation.
# Runs inside the one-shot urbangreen-ollama-init container.
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

# qwen3.5 is a thinking model: without the cap and /no_think below it streams a
# reasoning block first, which is how an automated call ends up hanging.
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
