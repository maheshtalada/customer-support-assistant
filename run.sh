#!/bin/bash
# One-shot local launch for the demo. Creates the venv on first run.
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "→ creating venv + installing deps (first run only)…"
  python3 -m venv .venv
  ./.venv/bin/pip install -q --upgrade pip
  ./.venv/bin/pip install -q -r requirements.txt
fi

# train NLU models if not present
if [ ! -f "app/nlu/models/intent_mlp.joblib" ]; then
  echo "→ training NLU models…"
  ./.venv/bin/python train_models.py
fi

echo "→ launching Streamlit at http://localhost:8501"
./.venv/bin/streamlit run ui/streamlit_app.py
