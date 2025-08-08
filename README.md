# cs_steambot
PS C:\Users\fearl\OneDrive\Desktop\DIY\cs_steambot> python fetcher.py

Follows the full scraping fallback sequence:
1) Steam API
2) Steam JavaScript scraping
3) Steam HTML scraping
4) Buff.163
5) CSFloat
- Prints clear and clean messages for each fallback step.
- Hides unnecessary API debug prints.
- Displays final price and SGD conversion.

******************************
skins that won't work due to rarity 
    "M4A4 | Howl (Factory New)"
    "AWP | Dragon Lore (Factory New)"
    "AK-47 | Gold Arabesque (Factory New)"

some key notes: 
Why the Steam Market webpage always has prices, but API may not:
    - The webpage dynamically loads data from various sources, including more recent listings, sales, and cached info.
    - The API endpoint is a quick summary and can fail if listings are sparse, or the server limits API access.
    - The market might have anti-scraping or API rate limits or restrictions that aren’t documented.
Steam Market uses JavaScript to load the price and listings dynamically after page load.
-   requests fetches only the initial HTML (which lacks the price).
-   BeautifulSoup parses that HTML — no price data is found there.

Added a mini user chatbot that interacts 
downside is that have to manually enter the config file
upgrade is that the moment the skin is added, no need add the wearity as it can auto search 
- Glove and knife abit wonky

add visualisation graph and maybe predictability graph
===================================================================================================

import requests     #import requests library for making HTTP requests (permission to act as a client when webscraping)

import time     # import time library to have pauses between requests so as not to overload the server and not act as a bot

Re libary 
Fuzzy input matching (e.g., user types ak47 redline instead of AK-47 | Redline):
    - Use re.search() to find if user input contains certain keywords regardless of case, spacing, or punctuation.
    - Text cleanup / normalization:
    -Strip unwanted characters, spaces, or formats from scraped names.
Validation:
Check if input matches a valid format, e.g., AK-47 | <skin name>.

import json # import json library to handle JSON data
    - using it when we are trying to manipulate the JSON data 
    - Parsing JSON responses from APIs.
    - Saving scraped data (e.g., skin names) to .json (optional if you're using Python configs instead).

from bs4 import BeautifulSoup # import BeautifulSoup from bs4 for scraping HTML content

import urllib.parse # import urllib.parse for URL encoding and decoding

def get_skin_price 
> getting the prices from steam API

def scrape_skin_price_from_script 
> scrapping for Javascript on the steam community website 

def scrape_skin_price_from_html
> try scrapping for HTML on the steam community website 

The reason why we try both javascript and html is because the webpage could be coded in either or 

def scrape_buff_price
> if failed, try scrapping from this website instead 

def scrape_csfloat_price
> if failed, try srapping from this website instead 

def get_usd_to_sgd_rate()
> get the convertion rate from USD TO SGD 

def convert_usd_to_sgd
> Convert to sgd with 2dp

    from rapidfuzz import process  # Fuzzy matching library for better user input handling 
    from config import skins, wears  # Import the skins and wears configuration from the config module
    from difflib import get_close_matches  # Import get_close_matches for fuzzy matching user input

def fuzzy_choice 
>  designed to make user input more flexible and forgiving, especially when users might mistype or slightly misspell their choice.
> prompt: a string to show the user.
> options: a list of choices (e.g. skin names, categories).
If input is a number (e.g. "2"), convert it to an index and return the selected option.
If input is a text string, use fuzzy matching (from difflib.get_close_matches) to find the closest match in the options list.
So even if the user types "awpp" instead of "AWP", it will still work.

def chatbot_interface()
> Main function to run the chatbot interface