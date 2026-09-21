"""Verified, no-login marketplace lookups for the CS2 price checker."""
from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import quote

import requests
from rapidfuzz import fuzz, process

Log = Callable[[str], None]
TIMEOUT = 12
HEADERS = {"User-Agent": "CS2-Skin-Price-Checker/2.0", "Accept": "application/json"}
_cache: Dict[str, Tuple[float, Dict[str, dict]]] = {}


@dataclass
class Quote:
    marketplace: str
    price: Optional[str]
    currency: str
    status: str
    url: str
    stock: Optional[int] = None
    sgd_estimate: Optional[str] = None


def _cached(name: str, ttl: int, fetch: Callable[[], Dict[str, dict]], log: Log) -> Dict[str, dict]:
    stored = _cache.get(name)
    if stored and time.monotonic() - stored[0] < ttl:
        log("   -> Using recent %s catalog." % name)
        return stored[1]
    catalog = fetch()
    _cache[name] = (time.monotonic(), catalog)
    return catalog


def _item_schema(log: Log) -> Dict[str, dict]:
    log("[Catalog] Loading valid CS2 skin names and wear conditions...")
    def fetch():
        response = requests.get("https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en/skins.json", headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status(); skins = response.json()
        if not isinstance(skins, list): raise ValueError("unexpected CS2 catalog response")
        names = {}
        for skin in skins:
            for wear in skin.get("wears", []):
                if skin.get("name") and wear.get("name"):
                    names["%s (%s)" % (skin["name"], wear["name"])] = skin
                    if skin.get("stattrak"):
                        names["StatTrak™ %s (%s)" % (skin["name"], wear["name"])] = skin
        return names
    return _cached("CS2 item", 86400, fetch, log)


def _skinport(log: Log) -> Dict[str, dict]:
    log("[Skinport] Downloading public USD price catalog...")
    def fetch():
        response = requests.get("https://api.skinport.com/v1/items", params={"app_id": 730, "currency": "USD", "tradable": 0}, headers={**HEADERS, "Accept-Encoding": "br"}, timeout=TIMEOUT)
        response.raise_for_status(); rows = response.json()
        if not isinstance(rows, list): raise ValueError("unexpected Skinport response")
        return {row["market_hash_name"]: row for row in rows if row.get("market_hash_name")}
    return _cached("Skinport", 300, fetch, log)


def _49skins(log: Log) -> Dict[str, dict]:
    log("[49Skins] Downloading public EUR stock snapshot...")
    def fetch():
        response = requests.get("https://api.49skins.com/api/public/prices", params={"game": "cs2"}, headers={**HEADERS, "Accept-Encoding": "gzip"}, timeout=TIMEOUT)
        response.raise_for_status(); rows = response.json()
        if not isinstance(rows, list): raise ValueError("unexpected 49Skins response")
        return {row["market_hash_name"]: row for row in rows if row.get("market_hash_name")}
    return _cached("49Skins", 60, fetch, log)


def _skincash(log: Log) -> Dict[str, dict]:
    log("[SkinCash] Downloading public USD price feed...")
    def fetch():
        response = requests.get("https://api.skincash.gg/v1/prices", headers={**HEADERS, "Accept-Encoding": "gzip"}, timeout=TIMEOUT)
        response.raise_for_status(); data = response.json()
        rows = data.get("items") if isinstance(data, dict) else data
        if not isinstance(rows, list): raise ValueError("unexpected SkinCash response")
        return {row["market_hash_name"]: row for row in rows if row.get("market_hash_name")}
    return _cached("SkinCash", 300, fetch, log)


def _url(base: str, name: str) -> str:
    return base + quote(name, safe="")


def _sgd_estimate(amount: float, currency: str, log: Log) -> Optional[str]:
    try:
        response = requests.get("https://api.frankfurter.dev/v2/rate/%s/sgd" % currency.lower(), headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status(); rate = response.json().get("rate")
        if not isinstance(rate, (int, float)): raise ValueError("unexpected FX response")
        return "approx. S$%.2f" % (amount * rate)
    except (requests.RequestException, ValueError):
        log("   ! FX conversion unavailable; retaining original %s price." % currency)
        return None


def _steam(name: str, log: Log) -> Quote:
    log("[Steam] Requesting SGD price summary...")
    url = _url("https://steamcommunity.com/market/listings/730/", name)
    try:
        response = requests.get("https://steamcommunity.com/market/priceoverview/", params={"country": "SG", "currency": "23", "appid": "730", "market_hash_name": name}, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status(); price = response.json().get("lowest_price")
        if price:
            log("   OK Steam returned a current SGD listing price.")
            return Quote("Steam Community Market", price, "SGD", "Verified public price summary", url)
        log("   - Steam has no price summary for this item.")
        return Quote("Steam Community Market", None, "SGD", "No current price summary", url)
    except (requests.RequestException, ValueError):
        log("   ! Steam did not respond in time; no Steam price is shown.")
        return Quote("Steam Community Market", None, "SGD", "Request unavailable", url)


def _resolve(query: str, names: List[str], log: Log) -> Tuple[Optional[str], List[str]]:
    exact = next((name for name in names if name.casefold() == query.casefold()), None)
    if exact: return exact, []
    def search_key(value: str) -> str:
        value = (value.casefold().replace("ak-47", "ak").replace("headshot", "head shot")
                 .replace("stat-track", "stattrak").replace("stat track", "stattrak")
                 .replace("stat trak", "stattrak"))
        for short, full in {r"\bfn\b": "factory new", r"\bmw\b": "minimal wear", r"\bft\b": "field tested", r"\bww\b": "well worn", r"\bbs\b": "battle scarred"}.items():
            value = re.sub(short, full, value)
        return re.sub(r"[^a-z0-9]+", " ", value).strip()
    normalized_query = search_key(query)
    matches = process.extract(query, names, scorer=fuzz.token_sort_ratio, processor=search_key, limit=4, score_cutoff=72)
    suggestions = [match[0] for match in matches]
    if "stattrak" in normalized_query:
        standard_names = [name for name in names if not name.startswith("StatTrak™")]
        standard_query = normalized_query.replace("stattrak", "").strip()
        standard_matches = process.extract(standard_query, standard_names, scorer=fuzz.token_sort_ratio, processor=search_key, limit=1, score_cutoff=86)
        if standard_matches and (not matches or matches[0][1] < 86):
            log("   ! No valid StatTrak version exists for this item. The standard variant is suggested.")
            return None, [standard_matches[0][0]]
    if not matches or matches[0][1] < 86:
        log("   ! I could not confidently identify one exact market item."); return None, suggestions
    if len(matches) > 1 and matches[0][1] - matches[1][1] < 4:
        log("   ! Your search is ambiguous; choose one of the suggestions."); return None, suggestions
    return matches[0][0], suggestions


def lookup(query: str, log: Log) -> dict:
    log("Looking up: %s" % query); log("Matching your words against the CS2 item catalog...")
    try:
        names = sorted(_item_schema(log)); log("   OK CS2 item catalog is ready.")
    except (requests.RequestException, ValueError):
        return {"item_name": None, "quotes": [], "suggestions": [], "message": "The item catalog is unavailable. Try again shortly."}
    item_name, suggestions = _resolve(query, names, log)
    if not item_name:
        return {"item_name": None, "quotes": [], "suggestions": suggestions, "message": "I need a more specific skin name before showing any price."}
    log("OK Matched exact market name: %s" % item_name)

    # Marketplace checks are intentionally run and logged in display order.
    quotes = [_steam(item_name, log)]
    try:
        skinport = _skinport(log).get(item_name); log("   OK Skinport catalog is ready.")
    except (requests.RequestException, ValueError):
        skinport = None; log("   ! Skinport is unavailable; it will not contribute a price.")
    if skinport and skinport.get("min_price") is not None:
        amount = skinport["min_price"]
        quotes.append(Quote("Skinport", "$%.2f" % amount, "USD", "Verified public catalog", skinport.get("item_page") or "https://skinport.com/market/730", skinport.get("quantity"), _sgd_estimate(amount, "USD", log)))
        log("OK Skinport returned an active USD listing price.")
    else:
        quotes.append(Quote("Skinport", None, "USD", "No active listing", "https://skinport.com/market/730")); log("- Skinport has no active listing for this exact item.")
    try:
        market49 = _49skins(log).get(item_name); log("   OK 49Skins catalog is ready.")
    except (requests.RequestException, ValueError):
        market49 = None; log("   ! 49Skins is unavailable; it will not contribute a price.")
    if market49 and isinstance(market49.get("min_price"), int):
        amount = market49["min_price"] / 100
        quotes.append(Quote("49Skins", "EUR %.2f" % amount, "EUR", "Verified public stock snapshot", _url("https://49skins.com/market?search=", item_name), market49.get("quantity"), _sgd_estimate(amount, "EUR", log)))
        log("OK 49Skins returned a live EUR listing price.")
    else:
        quotes.append(Quote("49Skins", None, "EUR", "No active listing", _url("https://49skins.com/market?search=", item_name))); log("- 49Skins has no active stock for this exact item.")
    try:
        skincash = _skincash(log).get(item_name); log("   OK SkinCash price feed is ready.")
    except (requests.RequestException, ValueError):
        skincash = None; log("   ! SkinCash is unavailable; it will not contribute a price.")
    if skincash and isinstance(skincash.get("price"), (int, float)):
        amount = skincash["price"]
        quotes.append(Quote("SkinCash", "$%.2f" % amount, "USD", "Verified public price feed", skincash.get("item_page") or "https://skincash.gg/en/market", skincash.get("quantity"), _sgd_estimate(amount, "USD", log)))
        log("OK SkinCash returned an active USD listing price.")
    else:
        quotes.append(Quote("SkinCash", None, "USD", "No active listing", "https://skincash.gg/en/market")); log("- SkinCash has no active listing for this exact item.")
    log("Check complete. Prices are shown only for exact source matches.")
    return {"item_name": item_name, "quotes": [asdict(item) for item in quotes], "suggestions": suggestions, "message": "Original marketplace prices are shown with a live SGD estimate where available."}
