from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


class ActionSearchRecipe(Action):
    def name(self) -> Text:
        return "action_search_recipe"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        ingredients = tracker.get_slot("ingredients")
        
        # --- API Call Placeholder ---
        # In the future, you will call your recipe database API here.
        if ingredients:
            dispatcher.utter_message(
                text=f"You got it! Based on your ingredients, here is a great recipe: 'Simple Chicken and Veggie Stir-fry'. It's healthy and affordable."
            )
            return [SlotSet("last_recipe_name", "Simple Chicken and Veggie Stir-fry")]
        else:
            dispatcher.utter_message(
                text="To find a recipe, please tell me what ingredients you have."
            )

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

        # --- API Call Placeholder ---
        # Here you will call your food healthiness database API.
        if food_item:
            health_info = {
                "asparagus": "Yes, asparagus is very healthy! It's rich in Vitamin K, B9, C, A, and E.",
                "lentils": "Lentils are very healthy; they are rich in antioxidants and protein.",
                "pizza": "Pizza can be unhealthy if it's high in processed meats and fat. A healthier alternative could be a whole-wheat pita pizza with lots of vegetables."
            }
            response = health_info.get(food_item.lower(), f"I'm sorry, I don’t know the food item '{food_item}' yet.")
            dispatcher.utter_message(text=response)
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

        # --- API Call Placeholder ---
        if last_recipe:
            explanation = f"Alright, the '{last_recipe}' is a great choice because it contains lean protein and lots of vitamins from the vegetables. It's low in fat and gives you sustained energy. Good luck cooking!"
            dispatcher.utter_message(text=explanation)
        else:
            dispatcher.utter_message(text="I don't have a recipe in context. Could you ask for a recipe first?")

        return []
