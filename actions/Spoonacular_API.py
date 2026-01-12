import requests
import random
import re
import typing

# def find_recipe(ingredients: typing.List[str], query_wish: str, api_key: str) -> typing.Tuple[str, typing.Optional[str], typing.Optional[int]]:
#     """
#     Fetches a recipe from the Spoonacular API. 
#     - If ingredients are provided, searches by ingredients.
#     - If only a wish is provided, searches by keyword.
#     - If neither are provided, fetches a random recipe.

#     Args:
#         ingredients (List[str]): A list of ingredient names (e.g., ["chicken", "broccoli"]).
#         query_wish (str): An optional keyword to refine the search (e.g., "healthy", "vegan").
#         api_key (str): Your personal API key for the Spoonacular API.

#     Returns:
#         A tuple containing:
#         - str: A user-friendly, formatted string containing the recipe or an error message.
#         - Optional[str]: The title of the recipe if found.
#         - Optional[int]: The ID of the recipe if found.
#     """
    
#     # --- Step 0: Sanitize Inputs ---
#     # Handle cases where inputs might be None, empty lists, or whitespace strings
#     if ingredients is None:
#         ingredients = []
    
#     # Filter out empty strings or strings with only spaces from the list
#     clean_ingredients = [i.strip() for i in ingredients if i and i.strip()]
    
#     # Clean the wish string (None if it's just whitespace)
#     clean_wish = query_wish.strip() if query_wish and query_wish.strip() else None

#     # --- Step 1: Determine Search Strategy ---
#     search_params = {
#         'apiKey': api_key,
#         'number': 10  # Get 10 recipes to randomize from
#     }

#     try:
#         # Logic Branching based on available parameters
#         if clean_ingredients:
#             # Scenario A: Ingredients are provided (Use original logic)
#             search_url = 'https://api.spoonacular.com/recipes/findByIngredients'
#             ingredients_str = ',+'.join(clean_ingredients)
            
#             search_params.update({
#                 'ingredients': ingredients_str,
#                 'ranking': 1,
#                 'ignorePantry': True,
#                 'instructionsRequired': True
#             })
#             # Add the wish query if it exists
#             if clean_wish:
#                 search_params['query'] = clean_wish

#         elif clean_wish:
#             # Scenario B: No ingredients, but a Wish/Query exists
#             search_url = 'https://api.spoonacular.com/recipes/complexSearch'
#             search_params.update({
#                 'query': clean_wish,
#                 'instructionsRequired': True,
#                 'addRecipeInformation': False # We fetch full info in Step 2
#             })

#         else:
#             # Scenario C: Both are empty (Get a totally random recipe)
#             search_url = 'https://api.spoonacular.com/recipes/random'
#             search_params.update({
#                 'number': 1 # Random endpoint just needs to return 1 valid one
#             })

#         # --- First API Call: Search for recipes ---
#         search_response = requests.get(search_url, params=search_params, timeout=10)
#         search_response.raise_for_status() # Check for HTTP errors
        
#         data = search_response.json()
        
#         # --- Normalize the Response ---
#         # Different endpoints return different JSON structures. We normalize them into a list.
#         recipes = []
#         if isinstance(data, list):
#             # findByIngredients returns a direct list
#             recipes = data
#         elif 'results' in data:
#             # complexSearch returns {'results': [...]}
#             recipes = data['results']
#         elif 'recipes' in data:
#             # random returns {'recipes': [...]}
#             recipes = data['recipes']

#         # Check if list is empty
#         if not recipes:
#             # Create a custom error message based on what was searched
#             if clean_wish:
#                 return f"😢 Sorry, I couldn't find any recipes matching '{clean_wish}'.", None, None
#             elif clean_ingredients:
#                 return f"😢 Sorry, I couldn't find any recipes using {', '.join(clean_ingredients)}.", None, None
#             else:
#                 return "😢 Sorry, I couldn't find any recipes at the moment.", None, None

#         # Pick a random recipe from the list
#         chosen_recipe_summary = random.choice(recipes)
#         recipe_id = chosen_recipe_summary.get('id')

#         if not recipe_id:
#             return "Error: Found recipes, but could not retrieve a valid recipe ID.", None, None

#         # --- Step 2: Get the full details for the chosen recipe ---
#         # (This part of the code remains intact as requested)
#         info_url = f'https://api.spoonacular.com/recipes/{recipe_id}/information'
#         info_params = {
#             'apiKey': api_key,           # Use the provided api_key
#             'includeNutrition': False    # Save API quota points
#         }

#         # --- Second API Call: Get recipe details ---
#         info_response = requests.get(info_url, params=info_params, timeout=10)
#         info_response.raise_for_status()
        
#         recipe_details = info_response.json()

#         # --- Step 3: Build the user-friendly output string ---
        
#         title = recipe_details.get('title', 'Untitled Recipe')
#         servings = recipe_details.get('servings', 'N/A')
#         ready_in = recipe_details.get('readyInMinutes', 'N/A')
#         source_url = recipe_details.get('sourceUrl', '#')

#         # Start building the output
#         output = f"🍲 Here's a recipe I found for you!\n\n"
#         output += f"**{title}**\n\n"
#         output += f"**Serves:** {servings}\n"
#         output += f"**Ready in:** {ready_in} minutes\n"
#         output += f"**Source:** {source_url}\n"

#         # Add ingredients
#         output += f"\n--- Ingredients ---\n"
#         if recipe_details.get('extendedIngredients'):
#             for ingredient in recipe_details['extendedIngredients']:
#                 output += f" * {ingredient.get('original', 'Unknown ingredient')}\n"
#         else:
#             output += "No ingredients listed.\n"
        
#         # Add instructions
#         output += f"\n--- Instructions ---\n"
#         instructions = recipe_details.get('instructions')
#         if instructions:
#             # Remove HTML tags (like <li>, <ol>, <b>)
#             clean_instructions = re.sub(r'<[^>]+>', '\n', instructions).strip()
#             # Fix potential double newlines
#             clean_instructions = re.sub(r'\n\s*\n', '\n', clean_instructions)
#             output += f"{clean_instructions}\n"
#         else:
#             output += "No instructions provided. Check the source URL for details.\n"
            
#         return output, title, recipe_id

#     except requests.exceptions.HTTPError as http_err:
#         # Handle specific HTTP errors
#         if http_err.response.status_code == 401:
#             message = ("Error: Authentication failed. Please check your Spoonacular API_KEY.\n"
#                        "You can get a free key from https://spoonacular.com/food-api")
#             return message, None, None
#         elif http_err.response.status_code == 402:
#             message = (f"Error: API quota exceeded. The Spoonacular free plan is limited.\n"
#                        f"Details: {http_err.response.json().get('message')}")
#             return message, None, None
#         else:
#             message = f"HTTP error occurred: {http_err} - {http_err.response.text}"
#             return message, None, None
#     except requests.exceptions.RequestException as e:
#         # Handle other errors like network issues, timeouts, etc.
#         return f"An error occurred during the API request: {e}", None, None
#     except Exception as e:
#         # Catch any other unexpected errors
#         return f"An unexpected error occurred: {e}", None, None

def get_recipe_nutrition(recipe_id: int, recipe_title: str, api_key: str) -> str:
    """
    Fetches nutritional information and a health score for a given recipe ID.

    Args:
        recipe_id (int): The Spoonacular ID of the recipe.
        recipe_title (str): The title of the recipe (for use in the output string).
        api_key (str): Your personal API key for the Spoonacular API.

    Returns:
        str: A formatted string explaining the recipe's healthiness and nutritional facts.
    """
    try:
        # --- Step 1: Get Health Score from the information endpoint ---
        info_url = f'https://api.spoonacular.com/recipes/{recipe_id}/information'
        info_params = {'apiKey': api_key, 'includeNutrition': False}
        
        info_response = requests.get(info_url, params=info_params, timeout=10)
        info_response.raise_for_status()
        
        recipe_info = info_response.json()
        health_score = recipe_info.get('healthScore', 0)

        # --- Step 2: Get Nutrition Facts from the nutrition widget endpoint ---
        nutrition_url = f'https://api.spoonacular.com/recipes/{recipe_id}/nutritionWidget.json'
        nutrition_params = {'apiKey': api_key}

        nutrition_response = requests.get(nutrition_url, params=nutrition_params, timeout=10)
        nutrition_response.raise_for_status()

        nutrition_data = nutrition_response.json()
        calories = nutrition_data.get('calories', 'N/A')
        carbs = nutrition_data.get('carbs', 'N/A')
        fat = nutrition_data.get('fat', 'N/A')
        protein = nutrition_data.get('protein', 'N/A')

        # --- Step 3: Build the explanation string ---
        
        # Part A: Health Score Explanation
        health_explanation = f"The recipe '{recipe_title}' has a health score of **{health_score} out of 100**.\n"
        if health_score >= 75:
            health_explanation += "This is a very healthy choice! It's well-balanced and likely rich in nutrients."
        elif health_score >= 50:
            health_explanation += "This is a reasonably healthy option. It provides a good balance of nutrients."
        else:
            health_explanation += "This might not be the healthiest option, but it can be enjoyed in moderation as part of a balanced diet."

        # Part B: Nutritional Facts
        nutritional_facts = (
            f"\n\n--- Nutritional Facts (per serving) ---\n"
            f" * **Calories:** {calories}\n"
            f" * **Carbohydrates:** {carbs}\n"
            f" * **Fat:** {fat}\n"
            f" * **Protein:** {protein}\n"
        )

        calc_explanation = f"\nThe Spoonacular health score is a nutrient-density rating from 0 to 100 that rewards fiber and vitamins while penalizing sodium, sugar, and saturated fats, meaning most recipes fall below 50 because they contain common levels of salt or fat that the strict algorithm considers less than perfectly nutritious.\n"

        return f"{health_explanation}{nutritional_facts}{calc_explanation}"

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 401:
            return "Error: Authentication failed. Please check your Spoonacular API_KEY."
        elif http_err.response.status_code == 402:
            return f"Error: API quota exceeded. Details: {http_err.response.json().get('message')}"
        else:
            return f"HTTP error occurred while fetching nutrition: {http_err}"
    except requests.exceptions.RequestException as e:
        return f"An error occurred during the API request for nutrition: {e}"
    except Exception as e:
        return f"An unexpected error occurred while fetching nutrition: {e}"
    


















import requests
import random
import typing
import re

def find_recipe(ingredients: typing.List[str], query_wish: str, api_key: str) -> typing.Tuple[str, typing.Optional[str], typing.Optional[int]]:
    """
    Fetches a recipe from the Spoonacular API. 
    - Combined Search: Can filter by ingredients, wish/keyword, AND meal type simultaneously.
    - Meal Types: Filters for either 'breakfast' or 'main course' (evening meal).
    """
    
    # --- Step 0: Static Meal Types ---
    # We select one randomly from the desired categories
    # meal_types = ["breakfast", ]
    chosen_type = "main course"
    
    # --- Step 1: Sanitize Inputs ---
    if ingredients is None:
        ingredients = []
    
    clean_ingredients = [i.strip() for i in ingredients if i and i.strip()]
    clean_wish = query_wish.strip() if query_wish and query_wish.strip() else None

    # --- Step 2: Determine Search Strategy ---
    search_params = {
        'apiKey': api_key,
        'number': 10,  # Fetch 10 to allow for random selection
        'instructionsRequired': True
    }

    try:
        # Scenario A & B: Ingredients and/or Wish provided
        if clean_ingredients or clean_wish:
            search_url = 'https://api.spoonacular.com/recipes/complexSearch'
            
            # This handles the combined logic:
            if clean_ingredients:
                search_params['includeIngredients'] = ','.join(clean_ingredients)
            
            if clean_wish:
                search_params['query'] = clean_wish
            
            # Apply the meal type filter
            search_params['type'] = chosen_type
            
            search_params.update({
                'addRecipeInformation': True,
                'fillIngredients': True
            })

        # Scenario C: Both are empty (Random recipe based on meal type)
        else:
            search_url = 'https://api.spoonacular.com/recipes/random'
            search_params.update({
                'number': 1,
                'tags': chosen_type
            })

        # --- First API Call: Search ---
        search_response = requests.get(search_url, params=search_params, timeout=10)
        search_response.raise_for_status()
        
        data = search_response.json()
        
        # Normalize response (complexSearch uses 'results', random uses 'recipes')
        recipes = data.get('results', data.get('recipes', []))

        if not recipes:
            error_details = []
            if clean_wish: error_details.append(f"wish: '{clean_wish}'")
            if clean_ingredients: error_details.append(f"ingredients: {', '.join(clean_ingredients)}")
            detail_str = " and ".join(error_details)
            return f"😢 No {chosen_type} recipes found matching {detail_str}.", None, None

        # Pick a random recipe from the results
        chosen_recipe_summary = random.choice(recipes)
        recipe_id = chosen_recipe_summary.get('id')

        if not recipe_id:
            return "Error: Found recipes, but could not retrieve a valid recipe ID.", None, None

        # --- Step 3: Get full details (Step 2 in original logic) ---
        info_url = f'https://api.spoonacular.com/recipes/{recipe_id}/information'
        info_params = {'apiKey': api_key, 'includeNutrition': False}

        info_response = requests.get(info_url, params=info_params, timeout=10)
        info_response.raise_for_status()
        recipe_details = info_response.json()

        # --- Step 4: Build output string ---
        title = recipe_details.get('title', 'Untitled Recipe')
        servings = recipe_details.get('servings', 'N/A')
        ready_in = recipe_details.get('readyInMinutes', 'N/A')
        source_url = recipe_details.get('sourceUrl', '#')

        output = f"🍲 Here's a recipe I found for you!\n\n"
        output += f"**{title}**\n\n"
        output += f"**Serves:** {servings}\n"
        output += f"**Ready in:** {ready_in} minutes\n"
        output += f"**Source:** {source_url}\n"

        # Ingredients
        output += f"\n--- Ingredients ---\n"
        if recipe_details.get('extendedIngredients'):
            for ingredient in recipe_details['extendedIngredients']:
                output += f" * {ingredient.get('original', 'Unknown ingredient')}\n"
        else:
            output += "No ingredients listed.\n"
        
        # Instructions
        output += f"\n--- Instructions ---\n"
        instructions = recipe_details.get('instructions')
        if instructions:
            clean_instructions = re.sub(r'<[^>]+>', '\n', instructions).strip()
            clean_instructions = re.sub(r'\n\s*\n', '\n', clean_instructions)
            output += f"{clean_instructions}\n"
        else:
            output += "No instructions provided. Check the source URL for details.\n"
            
        return output, title, recipe_id

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 401:
            return "Error: Authentication failed. Check your API_KEY.", None, None
        elif http_err.response.status_code == 402:
            return "Error: API quota exceeded.", None, None
        return f"HTTP error occurred: {http_err}", None, None
    except Exception as e:
        return f"An unexpected error occurred: {e}", None, None