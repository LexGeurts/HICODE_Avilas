import os
import re
import queue
import threading
import asyncio
import requests
import urllib.parse
import websockets
import subprocess
import time
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS

# 1. Initialize the Flask app FIRST
app = Flask(__name__, static_folder='frontend')
CORS(app)

# 2. Configuration & Queue
RASA_URL = "http://localhost:5005/webhooks/rest/webhook"
VIBEVOICE_WS_URL = "ws://127.0.0.1:3000/stream"
TARGET_VOICE = "en-Carter_man"
# Increased timeout for longer Rasa processing
RASA_TIMEOUT = 120

speech_queue = queue.Queue()

# 3. Text Cleaning Logic (Chunking Removed)
def clean_text_for_speech(text):
    # Remove URLs
    text = re.sub(r'http\S+', '', text)

    # Block Raw Errors from being spoken
    if "Client Error" in text or "400" in text or "api.nal.usda.gov" in text:
        print(f" [!] BLOCKED RAW ERROR: {text}")
        return "I am having trouble connecting to the database right now."

    # Remove non-ASCII and Markdown
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'\*\*|\*|#', '', text)

    # Handle Recipe Lists - Just minor cleanup, no structural changes
    if "--- Ingredients ---" in text:
        # We just clean up newlines so it flows as one block if needed,
        # but since we aren't chunking, we can leave natural breaks if the TTS supports it.
        # This regex replaces multiple spaces with single space.
        pass

    return " ".join(text.split())

# 4. Voice Generation Logic
async def talk_to_vibevoice(text, voice=TARGET_VOICE):
    if not text.strip(): return

    clean_msg = text.strip()

    params = urllib.parse.urlencode({"text": clean_msg, "cfg": "1.500", "steps": "5", "voice": voice})
    uri = f"{VIBEVOICE_WS_URL}?{params}"

    try:
        async with websockets.connect(uri) as websocket:
            # ffplay setup with low latency
            ffplay_cmd = ["ffplay", "-nodisp", "-autoexit", "-f", "s16le", "-ar", "24000",
                          "-ch_layout", "mono", "-probesize", "32", "-sync", "ext", "-"]
            player = subprocess.Popen(ffplay_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

            async for message in websocket:
                if isinstance(message, bytes):
                    try:
                        player.stdin.write(message)
                        player.stdin.flush()
                    except BrokenPipeError:
                        break

            # --- SILENCE PADDING FIX ---
            # 1.5 seconds of silence to prevent cutoff
            padding = b'\x00' * int(24000 * 2 * 1.5)
            if player.stdin:
                try:
                    player.stdin.write(padding)
                    player.stdin.flush()
                    time.sleep(0.5)  # Wait for buffer to clear
                    player.stdin.close()
                except (BrokenPipeError, OSError):
                    pass
            player.wait()

    except Exception as e:
        print(f"VibeVoice Error: {e}")


# 5. Background Worker (Updated)
def speech_worker():
    while True:
        raw_text = speech_queue.get()
        if raw_text is None: break

        clean_speech = clean_text_for_speech(raw_text)

        # Send the WHOLE message at once
        if clean_speech.strip():
            asyncio.run(talk_to_vibevoice(clean_speech))

        speech_queue.task_done()


threading.Thread(target=speech_worker, daemon=True).start()


# 6. Routes
@app.route('/api/send_message', methods=['POST'])
def send_message():
    message = request.json.get('message')
    try:
        # Increased timeout for longer Rasa processing
        response = requests.post(RASA_URL, json={"sender": "user", "message": message}, timeout=RASA_TIMEOUT)
        rasa_data = response.json()

        for item in rasa_data:
            if item.get("text"):
                speech_queue.put(item["text"])

        return jsonify({"messages": rasa_data})
    except Exception as e:
        print(f"Rasa Connection Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    app.run(port=5000, debug=True, use_reloader=False)