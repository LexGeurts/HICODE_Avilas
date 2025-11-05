import os
import requests
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


def get_ingredient_health_info(ingredient: str, api_key: str) -> str:
    """
    Analyzes an ingredient for its health benefits using the FoodData Central API.

    Args:
        ingredient (str): The name of the food ingredient to analyze.
        api_key (str): Your personal API key for the FDC API.

    Returns:
        str: A user-friendly string summarizing the health information.
    """
    # --- Step 1: Search for the food to get its FDC ID ---
    search_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    search_params = {
        "query": ingredient,
        "api_key": api_key,
        "pageSize": 1,  # We only need the top result
        "dataType": "Foundation,SR Legacy,Survey (FNDDS)"
    }

    try:
        response = requests.get(search_url, params=search_params)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        search_data = response.json()

        if not search_data.get("foods"):
            return f"Sorry, I couldn't find any information for '{ingredient}'."

        # Get the FDC ID from the first search result
        fdc_id = search_data["foods"][0]["fdcId"]

    except requests.exceptions.RequestException as e:
        return f"Error connecting to the API: {e}"
    except (KeyError, IndexError):
        return f"Could not retrieve a valid ID for '{ingredient}'."

    # --- Step 2: Use the FDC ID to get detailed nutrient information ---
    details_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
    details_params = {"api_key": api_key}

    try:
        response = requests.get(details_url, params=details_params)
        response.raise_for_status()
        food_details = response.json()
    except requests.exceptions.RequestException as e:
        return f"Error fetching details from the API: {e}"

    # --- Step 3: Analyze the nutrients and build a user-friendly report ---
    nutrients = {
        "beneficial": {},
        "less_healthy": {}
    }

    # Define which nutrients we care about
    # Nutrient names are based on the FDC API documentation
    BENEFICIAL_NUTRIENTS = [
        "Protein", "Fiber, total dietary", "Vitamin C, total ascorbic acid",
        "Vitamin A, RAE", "Vitamin D (D2 + D3)", "Vitamin K (phylloquinone)",
        "Calcium, Ca", "Iron, Fe", "Potassium, K"
    ]
    LESS_HEALTHY_NUTRIENTS = ["Sugars, total including NLEA", "Fatty acids, total saturated", "Sodium, Na"]

    for nutrient in food_details.get("foodNutrients", []):
        nutrient_name = nutrient.get("nutrient", {}).get("name")
        amount = nutrient.get("amount", 0)
        unit = nutrient.get("nutrient", {}).get("unitName", "").lower()

        # Standardize nutrient names for easier lookup
        if "Sugars" in nutrient_name: nutrient_name = "Sugars, total including NLEA"
        if "Saturated" in nutrient_name: nutrient_name = "Fatty acids, total saturated"
        if "Fiber" in nutrient_name: nutrient_name = "Fiber, total dietary"

        if nutrient_name in BENEFICIAL_NUTRIENTS:
            nutrients["beneficial"][nutrient_name] = f"{amount}{unit}"
        elif nutrient_name in LESS_HEALTHY_NUTRIENTS:
            nutrients["less_healthy"][nutrient_name] = f"{amount}{unit}"

    # --- Step 4: Determine if it's "healthy" and format the output ---
    
    # Get the food name early for our check
    food_name_lower = food_details.get("description", ingredient).lower()

    # --- MODIFICATION: Force fruits and vegetables to be "healthy" ---
    # This is a simple override list. A more robust solution might use
    # the food's category if available from the API.
    ALWAYS_HEALTHY_KEYWORDS = [
        "apple", "banana", "orange", "strawberry", "blueberry", "raspberry",
        "spinach", "broccoli", "carrot", "kale", "tomato", "avocado",
        "lettuce", "cucumber", "bell pepper", "onion", "garlic"
    ]

    is_healthy_override = False
    for item in ALWAYS_HEALTHY_KEYWORDS:
        if item in food_name_lower:
            is_healthy_override = True
            break
    # --- End of modification ---

    # Original heuristic
    sugars = float(nutrients.get("less_healthy", {}).get("Sugars, total including NLEA", "0g")[:-1])
    saturated_fat = float(nutrients.get("less_healthy", {}).get("Fatty acids, total saturated", "0g")[:-1])

    is_healthy_original = len(nutrients["beneficial"]) > len(nutrients["less_healthy"]) and sugars < 10 and saturated_fat < 5

    # Use override if it's true, otherwise use original logic
    is_healthy = is_healthy_override or is_healthy_original

    # Build the final output string
    food_name = food_details.get("description", ingredient).capitalize()
    if is_healthy:
        output = f"✅ {food_name} appears to be a healthy choice.\n\n"
        # If it was overridden (e.g., a fruit), provide a better explanation
        if is_healthy_override and not is_healthy_original:
            output += "It's a whole food like a fruit or vegetable. While it may contain natural sugars, it's packed with vitamins, fiber, and other essential nutrients.\n"
        else:
            output += f"It's a good source of several important nutrients and is relatively low in sugar and saturated fat.\n"
    else:
        output = f"⚠️ {food_name} might be a less healthy choice, best enjoyed in moderation.\n\n"
        output += "It may be high in sugars, saturated fats, or sodium, with fewer beneficial nutrients.\n"

    output += f"\n--- Nutrient Summary (per 100g) ---\n"

    if nutrients["beneficial"]:
        output += "\n👍 Key Beneficial Nutrients:\n"
        for name, value in nutrients["beneficial"].items():
            # Clean up the name for readability
            clean_name = name.split(',')[0]
            output += f"   - {clean_name}: {value}\n"

    if nutrients["less_healthy"]:
        output += "\n👎 Nutrients to be Mindful Of:\n"
        for name, value in nutrients["less_healthy"].items():
            clean_name = name.split(',')[0]
            output += f"   - {clean_name}: {value}\n"

    return output