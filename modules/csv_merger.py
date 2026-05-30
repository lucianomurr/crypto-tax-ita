"""
Gestione multi-CSV: salvataggio persistente in data/uploads/,
merge con deduplicazione per ID transazione, controllo completezza storico.
"""
import os
import io
import hashlib
from datetime import date

import pandas as pd

UPLOADS_DIR = "data/uploads"


# ── Persistenza su disco ──────────────────────────────────────────────────────

def ensure_uploads_dir() -> None:
    os.makedirs(UPLOADS_DIR, exist_ok=True)


def save_upload(buffer: bytes, filename: str) -> str:
    """Salva un CSV in data/uploads/. Ritorna il path completo."""
    ensure_uploads_dir()
    safe_name = _safe_filename(filename)
    path = os.path.join(UPLOADS_DIR, safe_name)
    with open(path, "wb") as f:
        f.write(buffer)
    return path


def remove_upload(filename: str) -> None:
    path = os.path.join(UPLOADS_DIR, filename)
    if os.path.exists(path):
        os.remove(path)


def list_uploads() -> list[dict]:
    """Lista dei CSV salvati con metadati (nome, size, mtime)."""
    ensure_uploads_dir()
    files = []
    for fname in sorted(os.listdir(UPLOADS_DIR)):
        if fname.endswith(".csv"):
            path = os.path.join(UPLOADS_DIR, fname)
            stat = os.stat(path)
            files.append({
                "filename": fname,
                "path": path,
                "size_kb": round(stat.st_size / 1024, 1),
                "mtime": stat.st_mtime,
            })
    return files


def uploads_fingerprint() -> str:
    """Hash dei file presenti — cambia se si aggiunge/rimuove un file."""
    uploads = list_uploads()
    key = "|".join(f"{u['filename']}:{u['mtime']}" for u in uploads)
    return hashlib.md5(key.encode()).hexdigest()


# ── Caricamento e merge ───────────────────────────────────────────────────────

def load_all_uploads() -> pd.DataFrame | None:
    """Carica e unisce tutti i CSV da data/uploads/. Ritorna None se vuoto."""
    from modules.csv_loader import load_coinbase_csv
    uploads = list_uploads()
    if not uploads:
        return None

    dfs = []
    errors = []
    for u in uploads:
        try:
            df = load_coinbase_csv(u["path"])
            df["_source_file"] = u["filename"]
            dfs.append(df)
        except Exception as e:
            errors.append(f"{u['filename']}: {e}")

    if not dfs:
        return None

    merged = merge_dataframes(dfs)
    return merged, errors


def load_from_buffer(buffer: bytes, filename: str) -> pd.DataFrame:
    """Carica un CSV da buffer in memoria (usato per anteprima prima di salvare)."""
    from modules.csv_loader import load_coinbase_csv_from_buffer
    return load_coinbase_csv_from_buffer(io.BytesIO(buffer))


def merge_dataframes(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Unisce più DataFrame normalizzati deduplicando per ID transazione.
    Fallback: deduplicazione per (timestamp, asset, quantity, tx_type).
    """
    combined = pd.concat(dfs, ignore_index=True)

    if "ID" in combined.columns and combined["ID"].notna().all():
        combined = combined.drop_duplicates(subset=["ID"])
    else:
        combined = combined.drop_duplicates(
            subset=["timestamp", "asset", "quantity", "tx_type"]
        )

    return combined.sort_values("timestamp").reset_index(drop=True)


# ── Controllo completezza storico ─────────────────────────────────────────────

def check_history(df: pd.DataFrame) -> list[str]:
    """
    Controlla se la cronologia potrebbe essere incompleta per il calcolo LIFO.
    Ritorna una lista di messaggi di avviso (vuota se tutto ok).
    """
    warnings = []
    if df.empty:
        return warnings

    earliest = df["date"].min()
    sell_types = {"SELL", "CONVERT"}

    sells = df[df["tx_type"].isin(sell_types)]
    if sells.empty:
        return warnings

    # Ci sono vendite ma i dati iniziano tardi?
    if earliest.year >= 2022:
        warnings.append(
            f"Il CSV più antico inizia il **{earliest.strftime('%d/%m/%Y')}**. "
            "Se hai acquistato crypto prima di questa data, il calcolo LIFO potrebbe "
            "essere errato. Aggiungi il CSV degli anni precedenti."
        )

    # Ci sono vendite prima del primo acquisto nel dataset?
    buy_types = {"BUY", "RECEIVE", "STAKING", "EARN"}
    first_buy = df[df["tx_type"].isin(buy_types)]["date"].min() if not df[df["tx_type"].isin(buy_types)].empty else None
    first_sell = sells["date"].min()

    if first_buy and first_sell < first_buy:
        warnings.append(
            f"Trovata una vendita ({first_sell.strftime('%d/%m/%Y')}) prima del primo "
            f"acquisto rilevato ({first_buy.strftime('%d/%m/%Y')}). "
            "Potrebbe mancare il CSV con gli acquisti precedenti."
        )

    return warnings


# ── Utilità ───────────────────────────────────────────────────────────────────

def _safe_filename(name: str) -> str:
    """Mantiene solo caratteri sicuri per il filesystem."""
    keep = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    return "".join(c if c in keep else "_" for c in name)


def file_summary(df: pd.DataFrame) -> dict:
    """Statistiche rapide su un DataFrame caricato."""
    if df is None or df.empty:
        return {}
    return {
        "transazioni": len(df),
        "asset": df["asset"].nunique(),
        "dal": df["date"].min().strftime("%d/%m/%Y"),
        "al": df["date"].max().strftime("%d/%m/%Y"),
        "anni": sorted(df["date"].apply(lambda d: d.year).unique().tolist()),
    }
