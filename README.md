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

to do tmr 
add cases and figure out the use of the config file or not just delete 
add visualisation graph and maybe predictability graph?
can move on to the next project le i think im quite happy with this.