#!/usr/bin/env python3
"""CLI entry point — alternativo alla dashboard Streamlit."""
import os
import sys
import pandas as pd

from config import COINBASE_CSV, EXCHANGE_RATES_CACHE, OUTPUT_RW, OUTPUT_RT
from modules.csv_loader import load_coinbase_csv
from modules.exchange_rates import get_ecb_rates
from modules.rw_report import compute_rw_data
from modules.rt_report import compute_rt_data


def main():
    print("=== Dichiarazione Crypto Italia – Report RT e RW ===\n")

    os.makedirs("output", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(COINBASE_CSV):
        print(f"ERRORE: file non trovato: {COINBASE_CSV}")
        print("Scarica il CSV da Coinbase → Menu → Strumenti → Rapporti")
        sys.exit(1)

    print(f"Caricamento CSV: {COINBASE_CSV}")
    df = load_coinbase_csv(COINBASE_CSV)
    print(f"  → {len(df)} transazioni caricate\n")

    print("Recupero tassi BCE EUR/USD...")
    rates = get_ecb_rates(EXCHANGE_RATES_CACHE)
    print(f"  → {len(rates)} tassi disponibili\n")

    print("Calcolo Quadro RW...")
    rw_df = compute_rw_data(df, rates)
    rw_df.to_csv(OUTPUT_RW, index=False)
    print(f"  → Salvato: {OUTPUT_RW}")
    print(rw_df.to_string(index=False))
    ivaca_tot = rw_df["IVACA_Dovuta_EUR"].sum()
    print(f"\n  IVACA TOTALE DOVUTA: € {ivaca_tot:.2f}\n")

    print("Calcolo Quadro RT (LIFO)...")
    rt = compute_rt_data(df, rates)

    if rt["errors"]:
        print("\n  AVVISI:")
        for e in rt["errors"]:
            print(f"  ⚠ {e}")

    if rt["disposals"].empty:
        print("\n  → Nessuna vendita nell'anno: Quadro RT non necessario.")
    else:
        rt["disposals"].to_csv(OUTPUT_RT, index=False)
        print(f"  → Salvato: {OUTPUT_RT}")
        s = rt["summary"]
        print(f"\n  Plusvalenze totali:    € {s['Totale_Plusvalenze_EUR']:.2f}")
        print(f"  Minusvalenze totali:   € {s['Totale_Minusvalenze_EUR']:.2f}")
        print(f"  Reddito netto:         € {s['Reddito_Netto_EUR']:.2f}")
        print(f"  Imposta dovuta (26%):  € {s['Imposta_Dovuta_EUR']:.2f}")

    print("\n=== Report completato ===")


if __name__ == "__main__":
    main()
