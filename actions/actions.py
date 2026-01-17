import os
import requests
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# Keep your existing Spoonacular imports
from actions.Spoonacular_API import find_recipe, get_recipe_nutrition

# --- API Keys ---
# REPLACE "YOUR_NEW_KEY_HERE" with your actual keys
FDC_API_KEY = os.environ.get("FDC_API_KEY", "YOUR_NEW_USDA_KEY_HERE")
SPOONACULAR_API_KEY = os.environ.get("SPOONACULAR_API_KEY", "YOUR_SPOONACULAR_KEY")


# --- 1. Recipe Search Action ---
class ActionSearchRecipe(Action):
    def name(self) -> Text:
        return "action_search_recipe"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        ingredients_raw = tracker.get_slot("ingredients")
        # Clean up ingredients list
        ingredients = [item.strip() for item in ingredients_raw.split(',')] if ingredients_raw else []
        query_wish = tracker.get_slot("query_wish") or ""

        if ingredients:
            # Check for valid key
            if "DEMO_KEY" in SPOONACULAR_API_KEY or not SPOONACULAR_API_KEY:
                dispatcher.utter_message(text="I cannot search for recipes because the Spoonacular API key is missing.")
                return []

            try:
                # Call your Spoonacular module
                recipe_output, recipe_title, recipe_id = find_recipe(ingredients, query_wish, SPOONACULAR_API_KEY)
                dispatcher.utter_message(text=recipe_output)

                if recipe_title:
                    return [SlotSet("last_recipe_name", recipe_title), SlotSet("last_recipe_id", recipe_id)]
            except Exception as e:
                print(f"Spoonacular Error: {e}")
                dispatcher.utter_message(text="I had trouble finding a recipe right now.")
        else:
            dispatcher.utter_message(text="To find a recipe, please tell me what ingredients you have.")

        return []


# --- 2. Health Check Action (USDA) ---
class ActionCheckHealthiness(Action):
    def name(self) -> Text:
        return "action_check_healthiness"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        food_item = tracker.get_slot("food_item")

        if not food_item:
            dispatcher.utter_message(text="Which food item do you want to know about?")
            return []

        if "DEMO_KEY" in FDC_API_KEY or not FDC_API_KEY:
            dispatcher.utter_message(text="My food database key is missing, so I can't check that item.")
            return []

        try:
            # --- THE FIX: Simpler Data Types ---
            # We stick to 'Foundation' and 'SR Legacy' to avoid URL encoding errors.
            params = {
                "query": food_item,
                "pageSize": 1,
                "api_key": FDC_API_KEY,
                "dataType": ["Foundation", "SR Legacy"]
            }

            url = "https://api.nal.usda.gov/fdc/v1/foods/search"
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("foods"):
                    food = data["foods"][0]
                    description = food.get("description", "Unknown food")
                    nutrients = food.get("foodNutrients", [])

                    # --- SMART CALORIE SEARCH ---
                    calories = None

                    # 1. Look for explicit KCAL first
                    for n in nutrients:
                        if "Energy" in n.get("nutrientName", "") and n.get("unitName") == "KCAL":
                            calories = n.get("value")
                            break

                    # 2. If KCAL not found, check for kJ and convert
                    if calories is None:
                        for n in nutrients:
                            if "Energy" in n.get("nutrientName", "") and n.get("unitName") == "kJ":
                                val = n.get("value")
                                if val:
                                    calories = int(val / 4.184)  # Conversion: 1 kcal = 4.184 kJ
                                break

                    if calories is not None:
                        msg = f"One hundred grams of {description.lower()} contains about {int(calories)} calories."
                    else:
                        msg = f"I found {description.lower()}, but the calorie data is missing."

                    dispatcher.utter_message(text=msg)
                else:
                    dispatcher.utter_message(text=f"I couldn't find any nutrition data for {food_item}.")
            else:
                # This prints the specific error to your terminal if it fails again
                print(f"USDA API Error: {response.status_code} - {response.text}")
                dispatcher.utter_message(text="I'm having trouble connecting to the food database right now.")

        except Exception as e:
            print(f"Action Exception: {e}")
            dispatcher.utter_message(text="I can't check the healthiness right now due to a connection error.")

        return []
# --- 3. Explain Recommendation Action ---
class ActionExplainRecommendation(Action):
    def name(self) -> Text:
        return "action_explain_recommendation"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        last_recipe = tracker.get_slot("last_recipe_name")
        last_recipe_id = tracker.get_slot("last_recipe_id")

        if last_recipe and last_recipe_id:
            if "DEMO_KEY" in SPOONACULAR_API_KEY:
                dispatcher.utter_message(text="I need a valid API key to explain the recipe.")
            else:
                try:
                    explanation = get_recipe_nutrition(last_recipe_id, last_recipe, SPOONACULAR_API_KEY)
                    dispatcher.utter_message(text=explanation)
                except Exception:
                    dispatcher.utter_message(text="I couldn't retrieve the nutritional details for that recipe.")
        else:
            dispatcher.utter_message(text="I don't have a recipe in context. Could you ask for a recipe first?")

        return []