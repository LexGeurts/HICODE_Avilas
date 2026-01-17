#!/bin/bash

# --- CONFIGURATION ---
# Ensure this path points exactly to your VibeVoice demo folder
VIBE_SCRIPT="./Voice engine/VibeVoice/demo/vibevoice_realtime_demo.py"
MODEL_NAME="microsoft/VibeVoice-Realtime-0.5B"
# ---------------------

cleanup() {
    echo ""
    echo "Stopping all servers..."
    # Removed RELAY_PID as it is no longer used
    kill $FLASK_PID $RASA_PID $ACTION_PID $VIBE_PID 2>/dev/null
    exit
}

trap cleanup INT

# 0. CLEANUP
# Ensures no old processes are hanging onto the ports
echo "Cleaning up ports 3000, 5000, 5005, 5055..."
lsof -ti :3000,5000,5005,5055 | xargs kill -9 2>/dev/null

# Activate virtual environment
source .venv/bin/activate

# 1. Start VibeVoice in MPS Mode
# This uses the M3 Pro GPU to prevent the 4% hang issue
if [ -f "$VIBE_SCRIPT" ]; then
    echo "Starting VibeVoice on MPS (M3 Pro)..."
    python "$VIBE_SCRIPT" --model_path "$MODEL_NAME" --device mps &
    VIBE_PID=$!
else
    echo "ERROR: Script not found: $VIBE_SCRIPT"
    exit 1
fi

# 2. Start Rasa Actions (The Bridge)
echo "Starting Rasa Action Server..."
rasa run actions &
ACTION_PID=$!

# 3. Start Rasa Core (The Brain)
# Increased timeouts to handle neural voice generation
echo "Starting Rasa Core..."
export SANIC_RESPONSE_TIMEOUT=300
rasa run --enable-api --cors "*" &
RASA_PID=$!

echo "Waiting for MPS model to warm up (25s)..."
sleep 25

# 4. Start Flask UI (Integrated with VibeVoice logic)
# This will now trigger en-Carter_man through your speakers
echo "Starting Chat Interface on http://localhost:5000..."
export FLASK_APP=app.py
# Using 'python app.py' instead of 'flask run' ensures our thread-safe
# use_reloader=False setting is respected
python app.py &
FLASK_PID=$!

echo "------------------------------------------------"
echo "ALL SYSTEMS LIVE!"
echo "Neural Voice: http://localhost:3000"
echo "Chat Interface: http://localhost:5000"
echo "------------------------------------------------"

wait