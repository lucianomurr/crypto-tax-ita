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


def get_cached_prices_for_year(
    tickers: list[str], tax_year: int
) -> dict[str, dict[str, float | None]]:
    """
    Legge SOLO dalla cache locale (nessuna chiamata di rete).
    Ritorna {ticker: {"start": prezzo_o_None, "end": prezzo_o_None}}.
    None indica che il prezzo non è in cache per quella data.
    """
    start_date = date(tax_year, 1, 1)
    end_date   = date(tax_year, 12, 31)
    cache      = _load_cache()
    results: dict[str, dict[str, float | None]] = {}

    for ticker in tickers:
        if ticker.upper() not in TICKER_TO_ID:
            continue
        start_price = _read_from_cache(ticker.upper(), start_date, cache)
        end_price   = _read_from_cache(ticker.upper(), end_date,   cache)
        results[ticker] = {"start": start_price, "end": end_price}

    return results


def check_prices_completeness(
    tickers: list[str], tax_year: int
) -> dict:
    """
    Controlla la completezza dei prezzi in cache per l'anno richiesto.
    Ritorna un dict con:
      - complete:      bool — tutti i prezzi presenti
      - missing_start: list[str] — ticker senza prezzo al 01/01
      - missing_end:   list[str] — ticker senza prezzo al 31/12
      - not_mapped:    list[str] — ticker non presenti in TICKER_TO_ID
      - cached:        dict      — i prezzi già in cache
    """
    cached     = get_cached_prices_for_year(tickers, tax_year)
    not_mapped = [t for t in tickers if t.upper() not in TICKER_TO_ID]
    missing_start = [t for t, v in cached.items() if v["start"] is None]
    missing_end   = [t for t, v in cached.items() if v["end"]   is None]

    return {
        "complete":      not missing_start and not missing_end,
        "missing_start": missing_start,
        "missing_end":   missing_end,
        "not_mapped":    not_mapped,
        "cached":        cached,
    }


def _read_from_cache(ticker: str, target_date: date, cache: dict) -> float | None:
    """Cerca il prezzo in cache risalendo fino a 5 giorni indietro (no rete)."""
    for days_back in range(6):
        key = _cache_key(ticker, target_date - timedelta(days=days_back))
        if key in cache:
            return cache[key]
    return None


def fetch_prices_for_rw(tickers: list[str], tax_year: int,
                        progress_callback=None) -> dict[str, dict[str, float | None]]:
    """
    Recupera prezzi al 01/01 e 31/12 per tutti i ticker.
    Usa la cache locale se disponibile, altrimenti chiama CoinGecko.
    Ritorna {ticker: {"start": prezzo_01gen, "end": prezzo_31dic}}.
    progress_callback(ticker, current, total) — opzionale per la UI.
    """
    start_date = date(tax_year, 1, 1)
    end_date   = date(tax_year, 12, 31)
    cache      = _load_cache()
    results: dict[str, dict[str, float | None]] = {}

    for i, ticker in enumerate(tickers):
        if progress_callback:
            progress_callback(ticker, i, len(tickers))
        results[ticker] = {
            "start": get_price_eur(ticker, start_date, cache),
            "end":   get_price_eur(ticker, end_date, cache),
        }

    return results


def fetch_missing_prices(
    missing_start: list[str], missing_end: list[str], tax_year: int,
    progress_callback=None
) -> dict[str, dict[str, float | None]]:
    """
    Scarica da CoinGecko SOLO i prezzi mancanti dalla cache.
    Più veloce di fetch_prices_for_rw quando la maggior parte è già in cache.
    """
    start_date = date(tax_year, 1, 1)
    end_date   = date(tax_year, 12, 31)
    cache      = _load_cache()

    to_fetch = list(set(missing_start) | set(missing_end))
    results: dict[str, dict[str, float | None]] = {}

    for i, ticker in enumerate(to_fetch):
        if progress_callback:
            progress_callback(ticker, i, len(to_fetch))
        start = (get_price_eur(ticker, start_date, cache)
                 if ticker in missing_start else
                 _read_from_cache(ticker.upper(), start_date, cache))
        end   = (get_price_eur(ticker, end_date, cache)
                 if ticker in missing_end else
                 _read_from_cache(ticker.upper(), end_date, cache))
        results[ticker] = {"start": start, "end": end}

    return results
