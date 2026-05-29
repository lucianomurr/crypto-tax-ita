import pandas as pd
from config import get_tax_params
from modules.exchange_rates import convert_to_eur

BUY_TYPES  = {"BUY", "RECEIVE", "STAKING", "EARN"}
SELL_TYPES = {"SELL", "SEND", "CONVERT"}


def compute_rw_data(
    df: pd.DataFrame,
    rates: dict,
    tax_year: int = None,
    market_prices: dict | None = None,
) -> pd.DataFrame:
    """
    Calcola i dati per il Quadro RW per ogni asset detenuto su Coinbase.

    Parametri:
        df             – DataFrame normalizzato da csv_loader
        rates          – tassi BCE (vuoto se CSV già in EUR)
        tax_year       – anno d'imposta (default: config.TAX_YEAR)
        market_prices  – {ticker: {"start": eur, "end": eur}} da CoinGecko
                         Se None o ticker mancante, usa ultima transazione come fallback
    """
    if tax_year is None:
        from config import TAX_YEAR
        tax_year = TAX_YEAR

    params = get_tax_params(tax_year)
    ivaca_rate   = params["ivaca_rate"]
    ivaca_min    = params["ivaca_min"]
    ivaca_applies = params["ivaca_applies"]

    start_date = pd.Timestamp(f"{tax_year}-01-01").date()
    end_date   = pd.Timestamp(f"{tax_year}-12-31").date()

    rows = []

    for asset in sorted(df["asset"].unique()):
        if asset == "EUR":
            continue

        asset_df = df[df["asset"] == asset].copy()

        # ── Quantità al 01/01 e 31/12 ──────────────────────────────────────
        buys_before  = asset_df[asset_df["tx_type"].isin(BUY_TYPES)  & (asset_df["date"] < start_date)]["quantity"].sum()
        sells_before = asset_df[asset_df["tx_type"].isin(SELL_TYPES) & (asset_df["date"] < start_date)]["quantity"].sum()
        qty_start    = max(0.0, buys_before - sells_before)

        buys_total  = asset_df[asset_df["tx_type"].isin(BUY_TYPES)  & (asset_df["date"] <= end_date)]["quantity"].sum()
        sells_total = asset_df[asset_df["tx_type"].isin(SELL_TYPES) & (asset_df["date"] <= end_date)]["quantity"].sum()
        qty_end     = max(0.0, buys_total - sells_total)

        if qty_start == 0 and qty_end == 0:
            continue

        currency = asset_df["price_currency"].iloc[0]
        mp = (market_prices or {}).get(asset, {})

        # ── Valore iniziale al 01/01 ────────────────────────────────────────
        value_start_eur = 0.0
        price_start_source = "n/d"
        if qty_start > 0:
            if mp.get("start") is not None:
                value_start_eur   = qty_start * mp["start"]
                price_start_source = "CoinGecko"
            else:
                value_start_eur, price_start_source = _fallback_value(
                    asset_df, qty_start, start_date, prefer_after=True, currency=currency, rates=rates
                )

        # ── Valore finale al 31/12 ──────────────────────────────────────────
        value_end_eur = 0.0
        price_end_source = "n/d"
        if qty_end > 0:
            if mp.get("end") is not None:
                value_end_eur   = qty_end * mp["end"]
                price_end_source = "CoinGecko"
            else:
                value_end_eur, price_end_source = _fallback_value(
                    asset_df, qty_end, end_date, prefer_after=False, currency=currency, rates=rates
                )

        # ── IVACA ───────────────────────────────────────────────────────────
        if ivaca_applies:
            ivaca_calc   = value_end_eur * ivaca_rate
            ivaca_dovuta = ivaca_calc if ivaca_calc >= ivaca_min else 0.0
        else:
            ivaca_calc = ivaca_dovuta = 0.0

        rows.append({
            "Asset":              asset,
            "Codice_Bene":        21,
            "Codice_Stato_Estero": "USA",
            "Codice_Titolo":      1,
            "Quota_Possesso_%":   100,
            "Criterio_Valore":    1,
            "Quantita_01gen":     round(qty_start, 8),
            "Prezzo_01gen_EUR":   round(mp.get("start") or 0, 4),
            "Valore_Iniziale_EUR": round(value_start_eur, 2),
            "Quantita_31dic":     round(qty_end, 8),
            "Prezzo_31dic_EUR":   round(mp.get("end") or 0, 4),
            "Valore_Finale_EUR":  round(value_end_eur, 2),
            "IVACA_Calcolata_EUR": round(ivaca_calc, 2),
            "IVACA_Dovuta_EUR":   round(ivaca_dovuta, 2),
            "Fonte_Prezzo":       price_end_source,
        })

    return pd.DataFrame(rows)


def _fallback_value(asset_df, qty, near_date, prefer_after, currency, rates):
    """Usa il prezzo dell'ultima transazione disponibile come fallback."""
    priced = asset_df[asset_df["price_orig"] > 0].sort_values("timestamp")
    if prefer_after:
        row = priced[priced["date"] >= near_date].head(1)
        if row.empty:
            row = priced.head(1)
    else:
        row = priced[priced["date"] <= near_date].tail(1)
        if row.empty:
            row = priced.tail(1)

    if row.empty:
        return 0.0, "n/d"

    price    = float(row["price_orig"].iloc[0])
    tx_date  = row["date"].iloc[0]
    try:
        return qty * convert_to_eur(price, currency, tx_date, rates), f"ultima TX ({tx_date})"
    except ValueError:
        return 0.0, "errore conversione"
