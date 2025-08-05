# Configs like skin names, thresholds, intervals
# List of CS2 skins to monitor
# config.py

# CS2 skins to monitor (grouped by weapon for readability)
SKINS = {
    "AKs": [
        "AK-47 | Redline (Field-Tested)",
        "AK-47 | Vulcan (Minimal Wear)"
    ],
    "AWPs": [
        "AWP | Asiimov (Field-Tested)",
        "AWP | Dragon Lore (Factory New)"
    ],
    "M4A1s": [
        "M4A1-S | Printstream (Factory New)",
    ],
    "M4A4s": [
        "M4A4 | Howl (Factory New)",
        "M4A4 | The Emperor (Minimal Wear)"
    ],
}

# Interval for price checks (in seconds)
INTERVAL = 8 * 60 * 60  # 8 hours

# Flat price alert thresholds — trigger if skin price drops below this
ALERT_THRESHOLDS = {
    "AWP | Asiimov (Field-Tested)": 40.00,
    "AK-47 | Redline (Field-Tested)": 10.00
}

# Percentage drop alert (future use: track % drop compared to previous price)
PRICE_DROP_PERCENT = 5.0  # Alert if drop exceeds 5%

# Steam currency setting (1 = USD, 8 = SGD, etc.)
# See: https://partner.steamgames.com/doc/store/pricing/currencies
CURRENCY = 8  # 1 = USD, 8 = SGD
