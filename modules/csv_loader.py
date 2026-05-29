import io
import pandas as pd

# Formato Coinbase EU (EUR, skiprows=3): prezzi con prefisso €
# Formato Coinbase US (USD, skiprows=7): prezzi numerici puri

TRANSACTION_TYPES = {
    # Acquisti
    "buy": "BUY",
    "advanced trade buy": "BUY",
    "retail simple price improvement": "BUY",
    # Vendite
    "sell": "SELL",
    "advanced trade sell": "SELL",
    # Conversioni
    "convert": "CONVERT",
    "retail simple dust": "CONVERT",
    # Ricevute / inviate
    "receive": "RECEIVE",
    "deposit": "RECEIVE",
    "send": "SEND",
    "withdrawal": "SEND",
    # Staking / rewards
    "staking income": "STAKING",
    "rewards income": "STAKING",
    "inflation reward": "STAKING",
    "learning reward": "EARN",
    "coinbase earn": "EARN",
    # Operazioni neutre (non spostano inventory fiscale)
    "retail staking transfer": "NEUTRAL",
    "retail unstaking transfer": "NEUTRAL",
    "asset migration": "NEUTRAL",
    "retail eth2 deprecation": "NEUTRAL",
    "subscription": "NEUTRAL",
    "eth2 deposit": "NEUTRAL",
}

# Mappatura colonne: nome normalizzato -> possibili nomi nel CSV
COL_MAP = {
    "timestamp": ["Timestamp"],
    "tx_type": ["Transaction Type"],
    "asset": ["Asset"],
    "quantity": ["Quantity Transacted"],
    "price_currency": ["Price Currency", "Spot Price Currency"],
    "price_raw": ["Price at Transaction", "Spot Price at Transaction"],
    "subtotal_raw": ["Subtotal"],
    "total_raw": ["Total (inclusive of fees and/or spread)"],
    "fees_raw": ["Fees and/or Spread"],
    "notes": ["Notes"],
}


def _clean_numeric(s) -> float:
    """Rimuove simboli di valuta (€, $) e converte in float."""
    if pd.isna(s):
        return 0.0
    return float(str(s).replace("€", "").replace("$", "").replace(",", "").strip() or 0)


def _detect_skiprows(filepath_or_buffer) -> int:
    """Determina il numero di righe da saltare cercando la riga con 'Transaction Type'."""
    if hasattr(filepath_or_buffer, "read"):
        content = filepath_or_buffer.read()
        filepath_or_buffer.seek(0)
        lines = content.decode("utf-8", errors="replace").splitlines()
    else:
        with open(filepath_or_buffer, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

    for i, line in enumerate(lines[:20]):
        if "Transaction Type" in line:
            return i
    return 0


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Rinomina colonne, pulisce tipi e aggiunge colonne derivate."""
    df.columns = df.columns.str.strip()

    # Rinomina usando COL_MAP
    rename = {}
    for norm_name, candidates in COL_MAP.items():
        for c in candidates:
            if c in df.columns:
                rename[c] = norm_name
                break

    df = df.rename(columns=rename)

    # Parsing timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["date"] = df["timestamp"].dt.date

    # Tipo transazione
    df["tx_type"] = (
        df["tx_type"].str.strip().str.lower().map(TRANSACTION_TYPES).fillna("OTHER")
    )

    # Quantity
    df["quantity"] = pd.to_numeric(df.get("quantity", 0), errors="coerce").fillna(0).abs()

    # Pulizia prezzi: rimuovi € / $
    for col in ("price_raw", "subtotal_raw", "total_raw", "fees_raw"):
        if col in df.columns:
            df[col] = df[col].apply(_clean_numeric)
        else:
            df[col] = 0.0

    # Colonna price_currency: normalizza
    if "price_currency" not in df.columns:
        df["price_currency"] = "USD"
    else:
        df["price_currency"] = df["price_currency"].fillna("USD").str.strip().str.upper()

    # Colonne esposte esternamente (sempre in EUR se il CSV è EU, altrimenti in valuta originale)
    df["price_orig"] = df["price_raw"]
    df["subtotal_orig"] = df["subtotal_raw"]
    df["total_orig"] = df["total_raw"]
    df["fees_orig"] = df["fees_raw"]

    if "notes" not in df.columns:
        df["notes"] = ""

    return df.sort_values("timestamp").reset_index(drop=True)


def load_coinbase_csv(filepath: str) -> pd.DataFrame:
    skip = _detect_skiprows(filepath)
    df = pd.read_csv(filepath, skiprows=skip, on_bad_lines="skip")
    return _normalize(df)


def load_coinbase_csv_from_buffer(buffer) -> pd.DataFrame:
    skip = _detect_skiprows(buffer)
    content = buffer.read()
    df = pd.read_csv(io.BytesIO(content), skiprows=skip, on_bad_lines="skip")
    return _normalize(df)
