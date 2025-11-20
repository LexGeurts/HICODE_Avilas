
from actions.FDC_API import *
from actions.Spoonacular_API import find_recipe, get_recipe_nutrition
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import os

# --- FDC API Key ---
FDC_API_KEY = os.environ.get("FDC_API_KEY", "DEMO_KEY")
SPOONACULAR_API_KEY = os.environ.get("SPOONACULAR_API_KEY", "DEMO_KEY")



class ActionSearchRecipe(Action):
    def name(self) -> Text:
        return "action_search_recipe"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        ingredients_raw = tracker.get_slot("ingredients")
        ingredients = [item.strip() for item in ingredients_raw.split(',')] if ingredients_raw else []
        query_wish = tracker.get_slot("query_wish") or "" # Use wish or empty string
        
        if ingredients:
            if SPOONACULAR_API_KEY == "DEMO_KEY":
                dispatcher.utter_message(text="The SPOONACULAR_API_KEY is not configured. Please set it to use this feature.")
                return []

            # Call the Spoonacular API
            recipe_output, recipe_title, recipe_id = find_recipe(ingredients, query_wish, SPOONACULAR_API_KEY)
            
            dispatcher.utter_message(text=recipe_output)

            if recipe_title:
                print('yes')
                return [SlotSet("last_recipe_name", recipe_title), SlotSet("last_recipe_id", recipe_id)]
                
        else:
            # This case should ideally be handled by the flow, but as a fallback:
            dispatcher.utter_message(text="To find a recipe, please tell me what ingredients you have.")

        return []


class ActionCheckHealthiness(Action):
    def name(self) -> Text:
        return "action_check_healthiness"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        food_item = tracker.get_slot("food_item")
        
        if food_item:
            if FDC_API_KEY == "DEMO_KEY":
                dispatcher.utter_message(text="The FDC_API_KEY is not configured. Please set it to use this feature.")
            else:
                health_info = get_ingredient_health_info(food_item, FDC_API_KEY)
                dispatcher.utter_message(text=health_info)
        else:
            dispatcher.utter_message(text="Which food item do you want to know about?")

        return []


class ActionExplainRecommendation(Action):
    def name(self) -> Text:
        return "action_explain_recommendation"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        last_recipe = tracker.get_slot("last_recipe_name")
        last_recipe_id = tracker.get_slot("last_recipe_id")

        if last_recipe and last_recipe_id:
            if SPOONACULAR_API_KEY == "DEMO_KEY":
                dispatcher.utter_message(text="The SPOONACULAR_API_KEY is not configured. Please set it to use this feature.")
            else:
                explanation = get_recipe_nutrition(last_recipe_id, last_recipe, SPOONACULAR_API_KEY)
                dispatcher.utter_message(text=explanation)
        else:
            dispatcher.utter_message(text="I don't have a recipe in context. Could you ask for a recipe first?")

        return []
