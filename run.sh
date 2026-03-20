#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run.sh — Launch the AI Sales Enablement Playbook Streamlit app.
#
# Prerequisites:
#   pip install -r requirements.txt
#
# Usage:
#   ./run.sh              # Launch the Streamlit app on port 8501
#   ./run.sh --port 8080  # Launch on a custom port
# ---------------------------------------------------------------------------

set -euo pipefail

# Resolve the project root directory relative to this script's location
# so the script works regardless of where it's called from
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory so Streamlit can find all modules
cd "$SCRIPT_DIR"

# Check that streamlit is installed before attempting to launch
if ! command -v streamlit &>/dev/null; then
    echo "Error: streamlit is not installed."
    echo "Install it with: pip install -r requirements.txt"
    exit 1
fi

echo "╔═══════════════════════════════════════════════╗"
echo "║   AI Sales Enablement Playbook                ║"
echo "║   Starting Streamlit app...                   ║"
echo "║   All tools running in mock mode (no API key) ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# Launch the Streamlit app, passing through any additional arguments
# (e.g., --port, --server.headless, etc.)
streamlit run app.py "$@"
