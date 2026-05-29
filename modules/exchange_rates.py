import io
import os
import requests
import pandas as pd

# BCE: serie giornaliera USD/EUR (quanti USD per 1 EUR)
BCE_API = (
    "https://data-api.ecb.europa.eu/service/data/EXR/"
    "D.USD.EUR.SP00.A?format=csvdata&startPeriod=2015-01-01"
)


def get_ecb_rates(cache_file: str) -> dict:
    """Restituisce {pd.Timestamp -> eur_per_usd}. Usa cache locale se disponibile."""
    if os.path.exists(cache_file):
        df = pd.read_csv(cache_file, index_col="DATE", parse_dates=True)
        return df["EUR_PER_USD"].to_dict()
    return _fetch_and_cache(cache_file)


def refresh_ecb_rates(cache_file: str) -> dict:
    """Forza il download ignorando la cache."""
    return _fetch_and_cache(cache_file)


def _fetch_and_cache(cache_file: str) -> dict:
    resp = requests.get(BCE_API, timeout=60)
    resp.raise_for_status()

    df = pd.read_csv(io.StringIO(resp.text))

    time_col = next((c for c in df.columns if "TIME" in c.upper() or "DATE" in c.upper()), None)
    val_col = next((c for c in df.columns if "OBS_VALUE" in c.upper() or "VALUE" in c.upper()), None)

    if not time_col or not val_col:
        raise ValueError(f"Colonne BCE non trovate. Colonne disponibili: {list(df.columns)}")

    df = df[[time_col, val_col]].rename(columns={time_col: "DATE", val_col: "EURUSD"})
    df["DATE"] = pd.to_datetime(df["DATE"])
    df = df.dropna(subset=["EURUSD"])
    df["EUR_PER_USD"] = 1.0 / df["EURUSD"].astype(float)
    df = df.set_index("DATE")

    os.makedirs(os.path.dirname(cache_file) if os.path.dirname(cache_file) else ".", exist_ok=True)
    df[["EUR_PER_USD"]].to_csv(cache_file)

    return df["EUR_PER_USD"].to_dict()


def usd_to_eur(amount_usd: float, tx_date, rates: dict) -> float:
    """Converte USD → EUR usando il tasso BCE del giorno (o giorno lavorativo precedente)."""
    if amount_usd == 0:
        return 0.0
    d = pd.Timestamp(tx_date)
    for _ in range(10):
        if d in rates:
            return amount_usd * float(rates[d])
        d -= pd.Timedelta(days=1)
    raise ValueError(f"Nessun tasso BCE trovato per la data {tx_date}")


def convert_to_eur(amount: float, currency: str, tx_date, rates: dict) -> float:
    """Converte un importo in EUR. Se già in EUR, ritorna direttamente."""
    if currency == "EUR":
        return amount
    if currency == "USD":
        return usd_to_eur(amount, tx_date, rates)
    raise ValueError(f"Valuta non supportata: {currency}")
