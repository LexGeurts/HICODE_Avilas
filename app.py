import os
import re
import queue
import threading
import asyncio
import requests
import urllib.parse
import websockets
import subprocess
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS

# 1. Initialize the Flask app FIRST
app = Flask(__name__, static_folder='frontend')
CORS(app)

# 2. Configuration & Queue
RASA_URL = "http://localhost:5005/webhooks/rest/webhook"
VIBEVOICE_WS_URL = "ws://127.0.0.1:3000/stream"
TARGET_VOICE = "en-Carter_man"
speech_queue = queue.Queue()

# 3. Text Cleaning Logic
def clean_text_for_speech(text):
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'\*\*|\*|#', '', text)
    if "--- Ingredients ---" in text:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        title = lines[0] if lines else "a recipe"
        text = f"I've found a recipe for {title}. The full details are now on your screen."
    return " ".join(text.split())

# 4. Voice Generation Logic
async def talk_to_vibevoice(text, voice=TARGET_VOICE):
    params = urllib.parse.urlencode({"text": text, "cfg": "1.500", "steps": "5", "voice": voice})
    uri = f"{VIBEVOICE_WS_URL}?{params}"
    try:
        async with websockets.connect(uri) as websocket:
            ffplay_cmd = ["ffplay", "-nodisp", "-autoexit", "-f", "s16le", "-ar", "24000",
                          "-ch_layout", "mono", "-probesize", "32", "-sync", "ext", "-"]
            player = subprocess.Popen(ffplay_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
            async for message in websocket:
                if isinstance(message, bytes):
                    try:
                        player.stdin.write(message)
                        player.stdin.flush()
                    except BrokenPipeError: break
            # Padding to prevent clipping
            padding = b'\x00' * int(24000 * 2 * 0.5)
            if player.stdin:
                player.stdin.write(padding)
                player.stdin.flush()
                player.stdin.close()
            player.wait()
    except Exception as e:
        print(f"VibeVoice Error: {e}")

# 5. Background Worker
def speech_worker():
    while True:
        raw_text = speech_queue.get()
        if raw_text is None: break
        clean_speech = clean_text_for_speech(raw_text)
        if clean_speech.strip():
            asyncio.run(talk_to_vibevoice(clean_speech))
        speech_queue.task_done()

threading.Thread(target=speech_worker, daemon=True).start()

# 6. Routes (Must come after 'app' is defined)
@app.route('/api/send_message', methods=['POST'])
def send_message():
    message = request.json.get('message')
    try:
        response = requests.post(RASA_URL, json={"sender": "user", "message": message}, timeout=60)
        rasa_data = response.json()
        for item in rasa_data:
            if item.get("text"):
                speech_queue.put(item["text"])
        return jsonify({"messages": rasa_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(port=5000, debug=True, use_reloader=False)