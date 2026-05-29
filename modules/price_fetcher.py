"""
Recupero prezzi storici da CoinGecko (API pubblica gratuita, no API key).
Endpoint: /api/v3/coins/{id}/history?date={DD-MM-YYYY}
Cache locale in data/price_cache.json per evitare chiamate ripetute.
"""
import json
import os
import time
from datetime import date, timedelta

import requests

CACHE_FILE = "data/price_cache.json"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Mappa ticker Coinbase → CoinGecko coin ID
TICKER_TO_ID: dict[str, str] = {
    "BTC":     "bitcoin",
    "ETH":     "ethereum",
    "ETH2":    "ethereum",          # staked ETH, stessa quotazione
    "SOL":     "solana",
    "ADA":     "cardano",
    "DOT":     "polkadot",
    "ATOM":    "cosmos",
    "MATIC":   "matic-network",
    "POL":     "matic-network",     # MATIC rinominato POL
    "DOGE":    "dogecoin",
    "SHIB":    "shiba-inu",
    "PEPE":    "pepe",
    "FLOKI":   "floki",
    "AAVE":    "aave",
    "MKR":     "maker",
    "COMP":    "compound-governance-token",
    "UNI":     "uniswap",
    "LINK":    "chainlink",
    "XLM":     "stellar",
    "XTZ":     "tezos",
    "EOS":     "eos",
    "ALGO":    "algorand",
    "VET":     "vechain",
    "NEAR":    "near",
    "OP":      "optimism",
    "RNDR":    "render-token",
    "GRT":     "the-graph",
    "AMP":     "amp-token",
    "FET":     "fetch-ai",
    "AUCTION": "bounce-token",
    "APE":     "apecoin",
    "SPELL":   "spell-token",
    "CLV":     "clover-finance",
    "ACH":     "alchemy-pay",
    "NU":      "nucypher",
    "CGLD":    "celo",
    "EURC":    "euro-coin",
    "ALEO":    "aleo",
    "ZETA":    "zetachain",
    "TNSR":    "tensor",
    "SWELL":   "swell-network",
    "VARA":    "vara-network",
    "ACS":     "access-protocol",
}


def _load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def _cache_key(ticker: str, d: date) -> str:
    return f"{ticker}_{d.isoformat()}"


_api_key: str | None = None  # impostato da set_api_key()


def set_api_key(key: str | None) -> None:
    """Imposta la CoinGecko Demo API key (opzionale)."""
    global _api_key
    _api_key = key.strip() if key else None


def _fetch_from_coingecko(coin_id: str, d: date) -> float | None:
    """Chiama CoinGecko e ritorna il prezzo in EUR per la data richiesta."""
    date_str = d.strftime("%d-%m-%Y")
    url = f"{COINGECKO_BASE}/coins/{coin_id}/history"
    headers = {"x-cg-demo-api-key": _api_key} if _api_key else {}
    params  = {"date": date_str, "localization": "false"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code == 429:
            wait = 12 if not _api_key else 4
            time.sleep(wait)
            resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("market_data", {}).get("current_price", {}).get("eur")
    except Exception:
        return None


def get_price_eur(ticker: str, target_date: date, cache: dict | None = None) -> float | None:
    """
    Ritorna il prezzo in EUR per ticker alla data target_date.
    Cerca prima in cache, poi su CoinGecko.
    Ritrova fino a 5 giorni indietro (weekend/festivi).
    Ritorna None se il ticker non è mappato o CoinGecko non ha dati.
    """
    coin_id = TICKER_TO_ID.get(ticker.upper())
    if not coin_id:
        return None

    if cache is None:
        cache = _load_cache()

    # Tenta la data esatta e fino a 5 giorni prima (weekend, festivi)
    for days_back in range(6):
        d = target_date - timedelta(days=days_back)
        key = _cache_key(ticker.upper(), d)
        if key in cache:
            return cache[key]

        price = _fetch_from_coingecko(coin_id, d)
        if price is not None:
            cache[key] = price
            _save_cache(cache)
            time.sleep(0.3 if _api_key else 1.2)
            return price

    return None


def fetch_prices_for_rw(tickers: list[str], tax_year: int,
                        progress_callback=None) -> dict[str, dict[str, float | None]]:
    """
    Recupera prezzi al 01/01 e 31/12 per tutti i ticker.
    Ritorna {ticker: {"start": prezzo_01gen, "end": prezzo_31dic}}.
    progress_callback(ticker, current, total) — opzionale per la UI.
    """
    start_date = date(tax_year, 1, 1)
    end_date   = date(tax_year, 12, 31)

    cache = _load_cache()
    results: dict[str, dict[str, float | None]] = {}

    for i, ticker in enumerate(tickers):
        if progress_callback:
            progress_callback(ticker, i, len(tickers))

        results[ticker] = {
            "start": get_price_eur(ticker, start_date, cache),
            "end":   get_price_eur(ticker, end_date, cache),
        }

    return results
