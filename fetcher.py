import requests #import requests library for making HTTP requests (permission to act as a client)
import time # import time library to have pauses between requests so as not to overload the server
import re # import re library for  pattern matching and text manipulation. 
import json # import json library to handle JSON data
from bs4 import BeautifulSoup # import BeautifulSoup from bs4 for scraping HTML content
import urllib.parse # import urllib.parse for URL encoding and decoding


def get_skin_price(skin_name: str) -> str: 
    url = "https://steamcommunity.com/market/priceoverview/" # Steam API endpoint for price overview
    params = {
        "country": "SG", 
        "currency": "1", # 1 for USD, change if needed
        "appid": "730", # CS:GO app ID
        "market_hash_name": skin_name # The full name of the skin, e.g., "AK-47 | Redline (Field-Tested)"
    }
    try:
        response = requests.get(url, params=params) # Make the API request
        data = response.json() # Parse the JSON response
    except Exception as e:
        print(f"Error during API request for '{skin_name}': {e}") 
        return None 

    price = data.get("lowest_price") 
    if price:
        print(f"API success for '{skin_name}', price: {price}") 
        return price
    else:
        print(f"API failed or price not found for '{skin_name}', trying JS scrape...") 
        return None


def scrape_skin_price_from_script(skin_name: str) -> str: # Scrape price using JavaScript-rendered content
    base_url = "https://steamcommunity.com/market/listings/730/" 
    skin_url = base_url + urllib.parse.quote(skin_name) # URL encode the skin name
    headers = {"User-Agent": "Mozilla/5.0"} # Set a user-agent to mimic a browser request

    print(f"🤖 Attempting to scrape JS for '{skin_name}'...") 
    try:
        response = requests.get(skin_url, headers=headers) # Fetch the webpage
        # Check if the request was successful
        if not response.ok:
            print(f"Failed to fetch webpage for '{skin_name}', status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception during JS fetch for '{skin_name}': {e}") # Handle any exceptions during the request
        return None

    soup = BeautifulSoup(response.text, "html.parser") # Parse the HTML content with BeautifulSoup

    for script in soup.find_all("script"): # Iterate through all script tags
        # Look for the specific JavaScript variable that contains the price data
        if script.string and "Market_LoadOrderSpread" in script.string: # Check if the script contains the price data
            # Extract the JSON data from the script
            json_text_match = re.search(r'Market_LoadOrderSpread\((\{.*?\})\);', script.string, re.DOTALL) # Use regex to find the JSON data
            # If the JSON data is found, parse it
            if json_text_match: 
                json_text = json_text_match.group(1) # Extract the matched JSON string
                try:
                    data = json.loads(json_text) 
                    lowest_price = data.get("lowest_sell_order") 
                    if lowest_price:
                        price_dollars = int(lowest_price) / 100 # Convert the price from cents to dollars
                        price_str = f"${price_dollars:.2f}" # Format the price as a string
                        # Print the success message with the price
                        print(f"JS scrape success for '{skin_name}', price: {price_str}")
                        return price_str
                    else:
                        print(f"Lowest sell order not found for '{skin_name}'") # If the price is not found in the JSON data
                except Exception as e:
                    print(f"JS scrape error for '{skin_name}': {e}") # Handle any exceptions during JSON parsing

    print(f"JS scrape failed for '{skin_name}', trying HTML scrape...") # If no price data was found in the JavaScript, try scraping the HTML
    return None


def scrape_skin_price_from_html(skin_name: str) -> str:
    base_url = "https://steamcommunity.com/market/listings/730/"
    skin_url = base_url + urllib.parse.quote(skin_name)
    headers = {"User-Agent": "Mozilla/5.0"}

    print(f"🤖 Attempting to scrape visible HTML for '{skin_name}'...")
    try:
        response = requests.get(skin_url, headers=headers) # Fetch the webpage
        # Check if the request was successful
        if not response.ok:
            print(f"Failed HTML fetch for '{skin_name}', status: {response.status_code}")
            return None
    except Exception as e:
        print(f"HTML scrape exception for '{skin_name}': {e}") # Handle any exceptions during the request
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    selectors = [
        ".market_listing_price.market_listing_price_with_fee",
        ".market_listing_price"
    ]

    for selector in selectors: # Iterate through the list of selectors
        tag = soup.select_one(selector) # Select the first matching element
        # If a tag is found, extract and clean the text
        if tag:
            text = tag.text.strip().replace("\n", "") # Clean the text by stripping whitespace and removing newlines
            if text:
                print(f"HTML scrape success for '{skin_name}', price: {text}") # Print the success message with the price
                return text

    print(f"HTML scrape failed for '{skin_name}', trying Buff.163...") # If no price data was found in the HTML, try scraping Buff.163
    return None


def scrape_buff_price(skin_name: str) -> str:
    print(f"🔄 Trying Buff.163 for '{skin_name}'...")
    try:
        search_url = f"https://buff.163.com/api/market/goods/sell_order?game=csgo&page_num=1&goods_name={urllib.parse.quote(skin_name)}"
        headers = {"User-Agent": "Mozilla/5.0"} # Set a user-agent to mimic a browser request
        r = requests.get(search_url, headers=headers) # Fetch the Buff.163 API
        data = r.json() 
        if data.get("code") == "OK": # Check if the API response is OK
            items = data["data"].get("items") # Get the list of items from the response
            if items:
                price_str = f"¥{items[0]['price']}" # Format the price as a string with the currency symbol
                print(f"Buff.163 scrape success for '{skin_name}', price: {price_str}") # Print the success message with the price
                return price_str # Return the price string
    except Exception as e: # Handle any exceptions during the request or parsing
        print(f"Buff.163 scrape error for '{skin_name}': {e}") #
    print(f"Buff.163 scrape failed for '{skin_name}', trying CSFloat...")
    return None


def scrape_csfloat_price(skin_name: str) -> str:
    print(f"🔄 Trying CSFloat for '{skin_name}'...") 
    try:
        search_url = f"https://csfloat.com/search?sort=price_asc&name={urllib.parse.quote(skin_name)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(search_url, headers=headers) # Fetch the CSFloat search page
        soup = BeautifulSoup(r.text, "html.parser") # Parse the HTML content with BeautifulSoup
        tag = soup.select_one(".card-price") # Select the first element with the class "card-price"
        if tag:
            price_text = tag.text.strip()
            print(f"CSFloat scrape success for '{skin_name}', price: {price_text}") # Print the success message with the price
            return price_text
    except Exception as e:
        print(f"CSFloat scrape error for '{skin_name}': {e}")
    print(f"CSFloat scrape failed for '{skin_name}'")
    return None


def get_usd_to_sgd_rate():
    try:
        r = requests.get("https://api.frankfurter.app/latest?from=USD&to=SGD") # Fetch the latest USD to SGD exchange rate
        return r.json()["rates"]["SGD"] # Extract the SGD rate from the JSON response
    except: #if the request fails or the rate is not found, use a manual fallback rate
        print("Using fallback rate 1.35")
        return 1.35


def convert_usd_to_sgd(price_str, rate=None):
    if not price_str: # If the price string is empty or None, return None
        return None
    match = re.search(r"[\d,.]+", price_str)  # Use regex to find the first occurrence of a number in the price string
    if not match:
        return None
    usd = float(match.group().replace(",", "")) # Convert the price string to a float, removing commas
    rate = rate or get_usd_to_sgd_rate() # If no rate is provided, fetch the latest USD to SGD rate
    return round(usd * rate, 2) # Round the converted price to 2 decimal places

from rapidfuzz import process # Fuzzy matching library for better user input handling 

from config import skins, wears # Import the skins and wears configuration from the config module
from difflib import get_close_matches # Import get_close_matches for fuzzy matching user input

def fuzzy_choice(prompt, options): # Function to prompt user for a choice with fuzzy matching
    print(prompt) 
    for i, opt in enumerate(options, 1): # Enumerate options for display
        print(f"{i}. {opt}") 
    while True:
        user_input = input("Your choice (number or name): ").strip() # Get user input and strip whitespace
        # If user inputs a number
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(options): # Check if the index is valid
                return options[idx]
        else:
            # Try fuzzy matching
            matches = get_close_matches(user_input, options, n=1, cutoff=0.5) # Find close matches to user input
            if matches:
                return matches[0]
        print("❌ Invalid choice. Try again.")

def chatbot_interface(): # Main function to run the chatbot interface
    print("👋 Welcome to the CS2 Skin Price Bot!")
    categories = list(skins.keys()) # List of categories (weapons, cases, knives, gloves)
    # Choose category
    category = fuzzy_choice("Select a category:", categories)

    # Handle knives differently (skin selection + skin name)
    if category == "KNIFE":
        knife_skin = fuzzy_choice("Select a knife skin:", skins["KNIFE"])
        skin_name = input(f"Enter the skin name for {knife_skin} (e.g., Marble Fade): ").strip()
        
        print("Wear conditions:")
        wear = fuzzy_choice("Select wear condition:", wears)

        skin_full_name = f"{knife_skin} | {skin_name} ({wear})"

    elif category == "CASES":
        # Cases usually don't have wear or skin name variants
        skin_full_name = fuzzy_choice("Select a case:", skins["CASES"])

    else:
        # Other categories: select skin then wear
        skin_choice = fuzzy_choice(f"Select a skin for {category}:", skins[category])
        print("Wear conditions:")
        wear = fuzzy_choice("Select wear condition:", wears)

        skin_full_name = f"{category} | {skin_choice} ({wear})"

    print(f"\n🔎 Looking up: {skin_full_name}")

    # Call your price fetching logic here, for example:
    price = get_skin_price(skin_full_name)
    if not price:
        price = scrape_skin_price_from_script(skin_full_name)
    if not price:
        price = scrape_skin_price_from_html(skin_full_name)
    if not price:
        price = scrape_buff_price(skin_full_name)
    if not price:
        price = scrape_csfloat_price(skin_full_name)

    if price:
        price_sgd = convert_usd_to_sgd(price)
        print(f"💰 Price for '{skin_full_name}': {price} ≈ SGD {price_sgd}")
    else:
        print(f"\n❌ Could not fetch price for '{skin_full_name}'.")

    print("✅ Done.\n")

if __name__ == "__main__":
    chatbot_interface()


    """
    skins_to_track = {
        "AK-47": [
            "AK-47 | Redline (Field-Tested)",
            "AK-47 | Vulcan (Minimal Wear)",
            "AK-47 | Gold Arabesque (Factory New)",
            "AK-47 | Case Hardened (Battle-Scarred)"
        ],
        "AWP": [
            "AWP | Asiimov (Field-Tested)",
            "AWP | Dragon Lore (Factory New)",
            "AWP | Graphite (Minimal Wear)"
        ],
        "M4A1-S": [
            "M4A1-S | Printstream (Factory New)",
            "M4A1-S | Hyper Beast (Minimal Wear)"
        ],
        "M4A4": [
            "M4A4 | Howl (Factory New)",
            "M4A4 | The Emperor (Minimal Wear)"
        ],
        "USP-S": [
            "USP-S | Kill Confirmed (Minimal Wear)",
            "USP-S | Orion (Field-Tested)"
        ],
         "CASES": [
            "Dreams & Nightmares Case",
            "Fracture Case",
            "Prisma 2 Case",
            "Snakebite Case",
            "Danger Zone Case",
        ]       
    }
    """

'''
    print("🎯 Fetching CS2 skin prices...")
    for category, skins in skins_to_track.items():
        print(f"\n📦 Category: {category}")
        for skin in skins:
            price = get_skin_price(skin)
            if not price:
                price = scrape_skin_price_from_script(skin)
            if not price:
                price = scrape_skin_price_from_html(skin)
            if not price:
                price = scrape_buff_price(skin)
            if not price:
                price = scrape_csfloat_price(skin)

            if price:
                price_sgd = convert_usd_to_sgd(price)
                print(f"  - {skin}: {price} ≈ SGD {price_sgd} ⬅️")
            else:
                print(f"  - {skin}: Price not available")
            print()    
            time.sleep(2)
        print()
    print("\n✅ All skin prices fetched.\n")
'''