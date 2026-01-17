#!/usr/bin/env python3
import asyncio
import websockets
import subprocess
import urllib.parse
import json
import sys

# --- CONFIGURATION ---
VIBEVOICE_WS_URL = "ws://127.0.0.1:3000/stream"
DEFAULT_VOICE = "en-Carter_man"


async def talk_to_vibevoice(text, voice=DEFAULT_VOICE):
    params = urllib.parse.urlencode({
        "text": text,
        "cfg": "1.500",
        "steps": "5",
        "voice": voice
    })
    uri = f"{VIBEVOICE_WS_URL}?{params}"

    try:
        async with websockets.connect(uri) as websocket:
            # OPTIMIZED FLAGS for M3 Pro + FFmpeg 8.0.1
            ffplay_cmd = [
                "ffplay", "-nodisp", "-autoexit",
                "-f", "s16le", "-ar", "24000", "-ch_layout", "mono",
                "-probesize", "32", "-sync", "ext", "-"
            ]

            player = subprocess.Popen(
                ffplay_cmd,
                stdin=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )

            print("Assistant speaking...", end="", flush=True)

            async for message in websocket:
                if isinstance(message, bytes):
                    try:
                        player.stdin.write(message)
                        player.stdin.flush()
                    except BrokenPipeError:
                        break
                else:
                    # Optional: Print logs if needed for debugging
                    pass

            # --- THE "LAST MILE" FIX ---
            # Added int() to fix the multiplication error
            # Increased to 0.5s (24000 samples/sec * 2 bytes/sample * 0.5 sec)
            padding_bytes = int(24000 * 2 * 0.5)
            silence_padding = b'\x00' * padding_bytes

            try:
                player.stdin.write(silence_padding)
                player.stdin.flush()
            except:
                pass

            # Signal EOF to ffplay so it knows no more data is coming
            if player.stdin:
                player.stdin.close()

            # Wait for ffplay to empty its internal buffer (the speech + the silence)
            player.wait()
            print(" Done.")

    except Exception as e:
        print(f"\n[Error]: {e}")


async def main():
    print("=== VibeVoice Realtime (M3 Pro) ===")
    print("Direct WebSocket Mode. Type 'exit' to quit.")

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input: continue
            if user_input.lower() in ["exit", "quit"]: break
            await talk_to_vibevoice(user_input)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)