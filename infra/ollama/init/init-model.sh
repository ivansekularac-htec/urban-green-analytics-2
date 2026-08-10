#!/bin/sh

set -eu

MODEL="${OLLAMA_MODEL:-qwen3.5:2b}"

if ollama show "${MODEL}" >/dev/null 2>&1; then
    echo "Ollama model ${MODEL} is already cached."
    exit 0
fi

echo "Pulling Ollama model ${MODEL}..."

attempt=1
max_attempts=5

while [ "${attempt}" -le "${max_attempts}" ]; do
    if ollama pull "${MODEL}"; then
        echo "Ollama model ${MODEL} pulled successfully."
        exit 0
    fi

    echo "Model pull failed (attempt ${attempt}/${max_attempts}). Retrying..."

    attempt=$((attempt + 1))
    sleep 10
done

echo "Failed to pull Ollama model ${MODEL} after ${max_attempts} attempts."
exit 1