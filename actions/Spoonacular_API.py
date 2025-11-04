import requests
import random
import re
import typing

def find_recipe(ingredients: typing.List[str], query_wish: str, api_key: str) -> typing.Tuple[str, typing.Optional[str]]:
    """
    Fetches a recipe from the Spoonacular API based on a list of ingredients
    and an optional query wish (e.g., "healthy").

    Args:
        ingredients (List[str]): A list of ingredient names (e.g., ["chicken", "broccoli"]).
        query_wish (str): An optional keyword to refine the search (e.g., "healthy", "vegan").
        api_key (str): Your personal API key for the Spoonacular API.

    Returns:
        A tuple containing:
        - str: A user-friendly, formatted string containing the recipe or an error message.
        - Optional[str]: The title of the recipe if found, otherwise None.
    """
    
    # --- Step 1: Find recipes by ingredients ---
    search_url = 'https://api.spoonacular.com/recipes/findByIngredients'
    
    # Format ingredients for the API: "chicken,+broccoli,+garlic"
    ingredients_str = ',+'.join(ingredients)
    
    search_params = {
        'apiKey': api_key,
        'ingredients': ingredients_str,
        'query': query_wish,           # Pass the "wish" as a general query
        'number': 10,                  # Get 10 recipes to randomize from
        'ranking': 1,                  # Maximize used ingredients
        'ignorePantry': True,          # Ignore common pantry items
        'instructionsRequired': True   # Only get recipes that have instructions
    }
    
    try:
        # --- First API Call: Search for recipes ---
        search_response = requests.get(search_url, params=search_params, timeout=10)
        search_response.raise_for_status() # Check for HTTP errors
        
        recipes = search_response.json()
        
        if not recipes:
            return f"😢 Sorry, I couldn't find any '{query_wish}' recipes using {', '.join(ingredients)}.", None

        # Pick a random recipe from the list
        chosen_recipe_summary = random.choice(recipes)
        recipe_id = chosen_recipe_summary.get('id')

        if not recipe_id:
            return "Error: Found recipes, but could not retrieve a valid recipe ID.", None

        # --- Step 2: Get the full details for the chosen recipe ---
        info_url = f'https://api.spoonacular.com/recipes/{recipe_id}/information'
        info_params = {
            'apiKey': api_key,           # Use the provided api_key (FIXED from original code)
            'includeNutrition': False  # Save API quota points
        }

        # --- Second API Call: Get recipe details ---
        info_response = requests.get(info_url, params=info_params, timeout=10)
        info_response.raise_for_status()
        
        recipe_details = info_response.json()

        # --- Step 3: Build the user-friendly output string ---
        
        title = recipe_details.get('title', 'Untitled Recipe')
        servings = recipe_details.get('servings', 'N/A')
        ready_in = recipe_details.get('readyInMinutes', 'N/A')
        source_url = recipe_details.get('sourceUrl', '#')

        # Start building the output
        output = f"🍲 Here's a recipe I found for you!\n\n"
        output += f"**{title}**\n\n"
        output += f"**Serves:** {servings}\n"
        output += f"**Ready in:** {ready_in} minutes\n"
        output += f"**Source:** {source_url}\n"

        # Add ingredients
        output += f"\n--- Ingredients ---\n"
        if recipe_details.get('extendedIngredients'):
            for ingredient in recipe_details['extendedIngredients']:
                output += f" * {ingredient.get('original', 'Unknown ingredient')}\n"
        else:
            output += "No ingredients listed.\n"
        
        # Add instructions
        output += f"\n--- Instructions ---\n"
        instructions = recipe_details.get('instructions')
        if instructions:
            # Remove HTML tags (like <li>, <ol>, <b>)
            clean_instructions = re.sub(r'<[^>]+>', '\n', instructions).strip()
            # Fix potential double newlines
            clean_instructions = re.sub(r'\n\s*\n', '\n', clean_instructions)
            output += f"{clean_instructions}\n"
        else:
            output += "No instructions provided. Check the source URL for details.\n"
            
        return output, title

    except requests.exceptions.HTTPError as http_err:
        # Handle specific HTTP errors
        if http_err.response.status_code == 401:
            message = ("Error: Authentication failed. Please check your Spoonacular API_KEY.\n"
                       "You can get a free key from https://spoonacular.com/food-api")
            return message, None
        elif http_err.response.status_code == 402:
            message = (f"Error: API quota exceeded. The Spoonacular free plan is limited.\n"
                       f"Details: {http_err.response.json().get('message')}")
            return message, None
        else:
            message = f"HTTP error occurred: {http_err} - {http_err.response.text}"
            return message, None
    except requests.exceptions.RequestException as e:
        # Handle other errors like network issues, timeouts, etc.
        return f"An error occurred during the API request: {e}", None
    except Exception as e:
        # Catch any other unexpected errors
        return f"An unexpected error occurred: {e}", None

# --- Example Usage (requires a valid Spoonacular API key) ---

# if __name__ == "__main__":
#     # IMPORTANT: Replace with your actual API key
#     MY_SPOONACULAR_KEY = "5f491dd56fb148d7b417dc3d1a4c4830"

#     my_ingredients = ["chicken", "broccoli", "garlic"]
#     my_wish = "healthy stir-fry"

#     recipe_string = find_recipe(my_ingredients, my_wish, MY_SPOONACULAR_KEY)
#     print(recipe_string)

#     print("\n" + "="*30 + "\n")

#     # Example of a failed search
#     failed_search = find_recipe(["xyzabc", "qwert"], "anything", MY_SPOONACULAR_KEY)
#     print(failed_search)
