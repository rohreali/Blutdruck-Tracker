"""
This module contains the various API calls
"""

import requests

def get_coordinate_from_nominatim(street, postal_code, city):
    """Get the coordinate from the Nominatim API.
    
    Args:
    - street (str): The street
    - postal_code (str): The zip code
    - city (str): The city

    Returns:
    - lat (float): The latitude
    - lon (float): The longitude
    - error_message (str): The error message in case of an error, otherwise None
    """

    # Set the URL (a constant in uppercase letters is a convention to indicate that it should not be changed)
    API_URL = "https://nominatim.openstreetmap.org/search"

    # Set agent in header, check https://operations.osmfoundation.org/policies/nominatim/
    headers = {
        "User-Agent": "MyContactAppW04 (wehs@zhaw.ch)"
    }
    
    # Set the parameters
    url_params = {
        "q": f'{street} {postal_code} {city}', 
        "format": "json"
    }

    # Send the request to the Nominatim API
    response = requests.get(API_URL, headers= headers, params=url_params)

    # Check the status code
    if response.status_code == 200:  # 200 means "OK"
        # Get the JSON response
        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon, ""
        
    # If the status code is not 200, it means that there was an error
    error_message = f"Nominatim API Error:" + response.text
    return None, None, error_message


def get_ai_poem(name, huggingface_token):
    """
    Get a poem from the Hugging Face API.

    Args:
    - name (str): The name to include in the poem
    - huggingface_token (str): The Hugging Face API token

    Returns:
    - res_text (str): The poem
    """

    # The API URL for the model you want to use
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"

    # Prompt for the poem
    AI_PROMPT = f"""Write a short german poem including the name '{name}'. The poem should be 4 lines long and include nature."""

    # A token is required to use the Hugging Face API
    headers = {
        "Authorization": f"Bearer {huggingface_token}"
    }

    # Replace "The future of AI is" with your input text
    data = {
        "inputs": AI_PROMPT
    }

    # Send a request to the API
    response = requests.post(API_URL, headers=headers, json=data)

    # Get the response text
    res_text = response.json()[0]['generated_text']

    # remove the input text
    res_text = res_text.replace(AI_PROMPT, "")

    # remove empty lines
    res_text = "\n".join([line for line in res_text.split("\n") if line.strip() != ""])

    return res_text