import requests
import time
import re
import json
from bs4 import BeautifulSoup
import urllib.parse


def get_skin_price(skin_name: str) -> str:
    url = "https://steamcommunity.com/market/priceoverview/"
    params = {
        "country": "SG",
        "currency": "1",
        "appid": "730",
        "market_hash_name": skin_name
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
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


def scrape_skin_price_from_script(skin_name: str) -> str:
    base_url = "https://steamcommunity.com/market/listings/730/"
    skin_url = base_url + urllib.parse.quote(skin_name)
    headers = {"User-Agent": "Mozilla/5.0"}

    print(f"🤖 Attempting to scrape JS for '{skin_name}'...")
    try:
        response = requests.get(skin_url, headers=headers)
        if not response.ok:
            print(f"Failed to fetch webpage for '{skin_name}', status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception during JS fetch for '{skin_name}': {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    for script in soup.find_all("script"):
        if script.string and "Market_LoadOrderSpread" in script.string:
            json_text_match = re.search(r'Market_LoadOrderSpread\((\{.*?\})\);', script.string, re.DOTALL)
            if json_text_match:
                json_text = json_text_match.group(1)
                try:
                    data = json.loads(json_text)
                    lowest_price = data.get("lowest_sell_order")
                    if lowest_price:
                        price_dollars = int(lowest_price) / 100
                        price_str = f"${price_dollars:.2f}"
                        print(f"JS scrape success for '{skin_name}', price: {price_str}")
                        return price_str
                    else:
                        print(f"Lowest sell order not found for '{skin_name}'")
                except Exception as e:
                    print(f"JS scrape error for '{skin_name}': {e}")

    print(f"JS scrape failed for '{skin_name}', trying HTML scrape...")
    return None


def scrape_skin_price_from_html(skin_name: str) -> str:
    base_url = "https://steamcommunity.com/market/listings/730/"
    skin_url = base_url + urllib.parse.quote(skin_name)
    headers = {"User-Agent": "Mozilla/5.0"}

    print(f"🤖 Attempting to scrape visible HTML for '{skin_name}'...")
    try:
        response = requests.get(skin_url, headers=headers)
        if not response.ok:
            print(f"Failed HTML fetch for '{skin_name}', status: {response.status_code}")
            return None
    except Exception as e:
        print(f"HTML scrape exception for '{skin_name}': {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    selectors = [
        ".market_listing_price.market_listing_price_with_fee",
        ".market_listing_price"
    ]

    for selector in selectors:
        tag = soup.select_one(selector)
        if tag:
            text = tag.text.strip().replace("\n", "")
            if text:
                print(f"HTML scrape success for '{skin_name}', price: {text}")
                return text

    print(f"HTML scrape failed for '{skin_name}', trying Buff.163...")
    return None


def scrape_buff_price(skin_name: str) -> str:
    print(f"🔄 Trying Buff.163 for '{skin_name}'...")
    try:
        search_url = f"https://buff.163.com/api/market/goods/sell_order?game=csgo&page_num=1&goods_name={urllib.parse.quote(skin_name)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(search_url, headers=headers)
        data = r.json()
        if data.get("code") == "OK":
            items = data["data"].get("items")
            if items:
                price_str = f"¥{items[0]['price']}"
                print(f"Buff.163 scrape success for '{skin_name}', price: {price_str}")
                return price_str
    except Exception as e:
        print(f"Buff.163 scrape error for '{skin_name}': {e}")
    print(f"Buff.163 scrape failed for '{skin_name}', trying CSFloat...")
    return None


def scrape_csfloat_price(skin_name: str) -> str:
    print(f"🔄 Trying CSFloat for '{skin_name}'...")
    try:
        search_url = f"https://csfloat.com/search?sort=price_asc&name={urllib.parse.quote(skin_name)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        tag = soup.select_one(".card-price")
        if tag:
            price_text = tag.text.strip()
            print(f"CSFloat scrape success for '{skin_name}', price: {price_text}")
            return price_text
    except Exception as e:
        print(f"CSFloat scrape error for '{skin_name}': {e}")
    print(f"CSFloat scrape failed for '{skin_name}'")
    return None


def get_usd_to_sgd_rate():
    try:
        r = requests.get("https://api.frankfurter.app/latest?from=USD&to=SGD")
        return r.json()["rates"]["SGD"]
    except:
        print("Using fallback rate 1.35")
        return 1.35


def convert_usd_to_sgd(price_str, rate=None):
    if not price_str:
        return None
    match = re.search(r"[\d,.]+", price_str)
    if not match:
        return None
    usd = float(match.group().replace(",", ""))
    rate = rate or get_usd_to_sgd_rate()
    return round(usd * rate, 2)


if __name__ == "__main__":
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
