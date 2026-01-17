import os
import asyncio
import websockets
import subprocess
import urllib.parse
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# Import your custom API modules
from actions.FDC_API import *
from actions.Spoonacular_API import find_recipe, get_recipe_nutrition

# --- API Keys ---
FDC_API_KEY = os.environ.get("FDC_API_KEY", "DEMO_KEY")
SPOONACULAR_API_KEY = os.environ.get("SPOONACULAR_API_KEY", "DEMO_KEY")


# --- 1. Voice Agent Action ---
class ActionVibeVoiceSpeak(Action):
    def name(self) -> str:
        return "action_vibevoice_speak"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        # 1. Check if the action is actually starting
        print("\n[ACTION LOG]: VibeVoice Speak Action Triggered!")

        # 2. Check if we found text
        bot_text = next((e.get("text") for e in reversed(tracker.events)
                         if e.get("event") == "bot" and e.get("text")), None)

        if not bot_text:
            print("[ACTION LOG]: ERROR - No bot text found in tracker events.")
            return []

        print(f"[ACTION LOG]: Sending text to VibeVoice: {bot_text[:50]}...")

        params = urllib.parse.urlencode({
            "text": bot_text,
            "cfg": "1.500",
            "steps": "5",
            "voice": "de-Spk0_man"
        })
        uri = f"ws://127.0.0.1:3000/stream?{params}"

        try:
            async with websockets.connect(uri) as ws:
                print("[ACTION LOG]: WebSocket Connection to Port 3000 OPEN.")

                # Optimized ffplay for MacOS M3
                ff_cmd = ["ffplay", "-nodisp", "-autoexit", "-f", "s16le", "-ar", "24000", "-ch_layout", "mono", "-"]

                player = subprocess.Popen(ff_cmd, stdin=subprocess.PIPE,
                                          stderr=subprocess.PIPE)  # Capture stderr for debugging

                async for msg in ws:
                    if isinstance(msg, bytes):
                        player.stdin.write(msg)

                player.stdin.write(b'\x00' * int(24000 * 2 * 0.5))
                player.stdin.close()
                player.wait()
                print("[ACTION LOG]: Audio Playback Finished.")
        except Exception as e:
            print(f"[ACTION LOG]: CONNECTION ERROR: {e}")

        return []


# --- 2. Recipe Search Action ---
class ActionSearchRecipe(Action):
    def name(self) -> Text:
        return "action_search_recipe"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        ingredients_raw = tracker.get_slot("ingredients")
        ingredients = [item.strip() for item in ingredients_raw.split(',')] if ingredients_raw else []
        query_wish = tracker.get_slot("query_wish") or ""

        if ingredients:
            if SPOONACULAR_API_KEY == "DEMO_KEY":
                dispatcher.utter_message(text="The SPOONACULAR_API_KEY is not configured.")
                return []

            recipe_output, recipe_title, recipe_id = find_recipe(ingredients, query_wish, SPOONACULAR_API_KEY)
            dispatcher.utter_message(text=recipe_output)

            if recipe_title:
                return [SlotSet("last_recipe_name", recipe_title), SlotSet("last_recipe_id", recipe_id)]
        else:
            dispatcher.utter_message(text="To find a recipe, please tell me what ingredients you have.")

        return []


# --- 3. Health Check Action ---
class ActionCheckHealthiness(Action):
    def name(self) -> Text:
        return "action_check_healthiness"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        food_item = tracker.get_slot("food_item")

        if food_item:
            if FDC_API_KEY == "DEMO_KEY":
                dispatcher.utter_message(text="The FDC_API_KEY is not configured.")
            else:
                health_info = get_ingredient_health_info(food_item, FDC_API_KEY)
                dispatcher.utter_message(text=health_info)
        else:
            dispatcher.utter_message(text="Which food item do you want to know about?")

        return []


# --- 4. Explain Recommendation Action ---
class ActionExplainRecommendation(Action):
    def name(self) -> Text:
        return "action_explain_recommendation"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        last_recipe = tracker.get_slot("last_recipe_name")
        last_recipe_id = tracker.get_slot("last_recipe_id")

        if last_recipe and last_recipe_id:
            if SPOONACULAR_API_KEY == "DEMO_KEY":
                dispatcher.utter_message(text="The SPOONACULAR_API_KEY is not configured.")
            else:
                explanation = get_recipe_nutrition(last_recipe_id, last_recipe, SPOONACULAR_API_KEY)
                dispatcher.utter_message(text=explanation)
        else:
            dispatcher.utter_message(text="I don't have a recipe in context. Could you ask for a recipe first?")

        return []