# CLAUDE.md — Crypto Tax IT

Leggi questo file prima di modificare qualsiasi cosa. Per la documentazione utente vedi `README.md`; per le regole fiscali vedi `docs/`.

---

## Entry point

```bash
streamlit run app.py   # dashboard
python main.py         # CLI (richiede data/coinbase_export.csv)
pytest tests/ -v       # test suite
```

---

## Architettura e flusso dati

```
CSV Coinbase
    → csv_loader.load_coinbase_csv_from_buffer()
    → DataFrame normalizzato
    → compute_rw_data(df, rates, tax_year, market_prices)  →  rw_df
    → compute_rt_data(df, rates, tax_year)                 →  rt dict
    → generate_rw_excel(rw_df, df, tax_year)               →  BytesIO
```

Moduli puri (nessun `st.*`, nessun side effect): `csv_loader`, `exchange_rates`, `lifo_engine`, `rw_report`, `rt_report`, `excel_report`. Tenerli così.

`app.py` è l'unico punto dove vive Streamlit. Se supera ~1000 righe, estrai i tab in `ui/tab_*.py`.

---

## Regole — Scalabilità

- `st.session_state` keys in uso: `df`, `uploaded_filename`, `available_years`, `rates`, `market_prices_{year}`. Non aggiungerne senza motivo.
- Cache CoinGecko: dizionario piatto `{ticker_date: price}` in JSON. Oltre ~5000 voci → valuta SQLite.
- `LIFOEngine` è in RAM. Per >100k transazioni valuta chunking.
- Evita `.iterrows()` su DataFrame grandi: usa operazioni vettoriali.
- `pd.ExcelWriter` + `openpyxl` è lento oltre 500 righe → valuta `xlsxwriter`.

## Regole — Sicurezza

- `.env` non va mai committato. La API key CoinGecko non va mai loggata né mostrata in UI.
- Il CSV caricato viene letto solo in memoria, mai scritto su disco dalla dashboard.
- Nessun `eval()` o `exec()`.
- Tutte le chiamate HTTP hanno `timeout=` esplicito e `try/except`.
- Valida sempre l'input esterno al boundary (`csv_loader.py`).

## Regole — Disclaimer

Non rimuovere né attenuare il disclaimer in `README.md`, `LICENSE` e nella sidebar di `app.py`. È parte integrante del progetto.

---

## Invarianti fiscali — non rompere mai

- Metodo **LIFO**: gli ultimi lotti acquistati sono i primi venduti.
- **Quadro RW** obbligatorio anche senza vendite, se si detiene al 31/12.
- **Colonna 4 (Stato estero) = vuoto** per le cripto-attività (Circ. ADE 30/E/2023).
- `SELL` e `CONVERT` sono entrambi eventi tassabili nel Quadro RT.
- La franchigia è una **soglia**: se netto < franchigia → imposta = 0 (non deduzione parziale).
- IVACA non dovuta se importo < €12 per rigo. Non esiste per anni ≤ 2022.
- Minusvalenze crypto pre-2023 non compensabili con plusvalenze post-2023.
- Parametri per anno in `config.get_tax_params()` — non hardcodare aliquote nel codice.

---

## Formato CSV Coinbase (europeo)

```
riga 0: "Transactions"
riga 1: "User,Nome,UUID"
riga 2: header colonne  ← skiprows=3
```

Colonne normalizzate rilevanti dopo `csv_loader`:

| Colonna | Tipo | Note |
|---|---|---|
| `timestamp` | datetime tz-aware (UTC) | **Non scrivere in Excel** → usa `date` |
| `date` | datetime.date | Sicuro per Excel |
| `tx_type` | str | BUY/SELL/CONVERT/RECEIVE/SEND/STAKING/EARN/NEUTRAL/OTHER |
| `price_currency` | str | EUR o USD |
| `price_orig` | float | Prezzo pulito da € / $ |
| `subtotal_orig` | float | Importo netto (senza fee) — usato per i ricavi RT |
| `total_orig` | float | Importo totale (con fee) — usato come costo acquisto |

Nuovi tipi TX non mappati → `OTHER`. Aggiungere in `csv_loader.TRANSACTION_TYPES`.

---

## Excel output (formato standard)

Generato da `excel_report.generate_rw_excel()`. Due fogli fissi:

- **Riassunto**: una riga per exchange + riga "Complessivo"
- **Coinbase**: una riga per asset con quantità×2, prezzo×2, valore×2, IC, giorni

Colonne e ordine definiti in `docs/02_quadro_rw.md`. Non cambiare senza aggiornare la doc.

---

## Backlog

- [ ] Supporto wallet personali (rigo RW separato)
- [ ] Supporto multi-exchange (Binance, Kraken…)
- [ ] Export PDF scheda compilazione
- [ ] `@st.cache_data` su `compute_rw_data` e `compute_rt_data`
- [ ] Inserimento manuale prezzi al 01/01 e 31/12 come override CoinGecko
