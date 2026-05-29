# CLAUDE.md — Crypto Tax IT

Guida per Claude Code su questo progetto. Leggi questo file integralmente prima di toccare qualsiasi cosa.

---

## Contesto del progetto

Dashboard Streamlit per la dichiarazione fiscale italiana di cripto-attività (Quadri RT e RW / Riquadri T e W del 730). Pensata per contribuenti residenti fiscalmente in Italia con exchange principale Coinbase (CSV in formato europeo, valuta EUR).

**Stack**: Python 3.10+, Streamlit, Pandas, Plotly, openpyxl, requests, python-dotenv.  
**Entry point dashboard**: `streamlit run app.py`  
**Entry point CLI**: `python main.py`

---

## Architettura

```
docs/                   ← Regole fiscali e normativa (leggere prima di modificare logica di calcolo)
  01_normativa.md       ← Quadro legislativo e parametri per anno
  02_quadro_rw.md       ← Campi RW, calcolo IVACA, giorni detenzione
  03_quadro_rt.md       ← Metodo LIFO, plusvalenze, compensazione minusvalenze
  04_tipi_transazione.md ← Trattamento fiscale per ogni tipo operazione Coinbase
  05_scadenze_sanzioni.md ← Scadenze, codici F24, sanzioni, ravvedimento
  06_checklist.md       ← Checklist annuale pre-dichiarazione
app.py                  ← UI Streamlit (unico file, ~900 righe)
config.py               ← parametri fiscali per anno (get_tax_params)
main.py                 ← CLI alternativa alla dashboard
modules/
  csv_loader.py         ← parsing CSV Coinbase EU/US, normalizzazione
  exchange_rates.py     ← tassi BCE EUR/USD, cache CSV locale
  lifo_engine.py        ← motore LIFO (Lot, Disposal, LIFOEngine)
  price_fetcher.py      ← prezzi storici CoinGecko, cache JSON locale
  rw_report.py          ← Quadro RW + IVACA (compute_rw_data)
  rt_report.py          ← Quadro RT + plusvalenze LIFO (compute_rt_data)
  excel_report.py       ← Excel formato standard (generate_rw_excel)
data/
  exchange_rates.csv    ← cache tassi BCE (auto-generato)
  price_cache.json      ← cache prezzi CoinGecko (auto-generato)
output/                 ← report CLI
.env                    ← COINGECKO_API_KEY (non committare)
```

### Flusso dati

```
CSV Coinbase
    ↓ csv_loader.load_coinbase_csv_from_buffer()
DataFrame normalizzato (colonne: timestamp, date, tx_type, asset,
    quantity, price_currency, price_orig, subtotal_orig, total_orig,
    fees_orig, notes)
    ↓
compute_rw_data(df, rates, tax_year, market_prices)  →  rw_df
compute_rt_data(df, rates, tax_year)                 →  rt dict
    ↓
generate_rw_excel(rw_df, df, tax_year)               →  BytesIO Excel
```

---

## Regole di sviluppo

### Scalabilità
- `app.py` è già lungo. Se supera ~1000 righe considera di estrarre i tab in moduli separati (`ui/tab_overview.py`, ecc.) e importarli.
- Le funzioni di calcolo (`compute_rw_data`, `compute_rt_data`) devono restare **pure** (nessun side effect, nessun `st.*`): ricevono dati, restituiscono dati.
- La cache CoinGecko (`data/price_cache.json`) è un dizionario piatto `{ticker_date: price}`. Se cresce oltre ~5000 voci, valuta SQLite.
- Il `LIFOEngine` tiene tutto in RAM. Per dataset enormi (>100k transazioni) valuta chunking o un motore basato su database.
- `st.session_state` viene usato per: `df`, `uploaded_filename`, `available_years`, `rates`, `market_prices_{year}`. Non aggiungere stato senza una ragione precisa — ogni chiave in più è un bug potenziale al reset.

### Sicurezza
- **`.env` non va mai committato**. Aggiungi sempre `.env` e `data/` al `.gitignore` prima di fare qualsiasi push.
- La API key CoinGecko viene letta con `os.getenv()` dopo `load_dotenv()`. Non loggarla mai, non includerla in messaggi di errore, non stamparla in UI.
- Il CSV caricato dall'utente viene letto in memoria e mai scritto su disco dalla dashboard. Mantieni questo invariante.
- I moduli non accettano input dall'utente direttamente: la validazione avviene in `csv_loader.py` (normalizzazione tipi, `on_bad_lines="skip"`). Se aggiungi nuovi input, valida sempre al boundary.
- Non usare `eval()` o `exec()` in nessun modulo.
- Le chiamate HTTP (BCE, CoinGecko) hanno sempre `timeout=` esplicito. Non rimuoverlo. Aggiungi `try/except` attorno a ogni chiamata di rete.

### Performance
- I calcoli pesanti (`compute_rw_data`, `compute_rt_data`) girano ad ogni cambio di anno o ricarica del CSV. Se diventano lenti, wrappali con `@st.cache_data` passando come chiave `(uploaded_filename, selected_year)`.
- I prezzi CoinGecko sono già cachati in JSON. Non fare fetch se la chiave `{ticker}_{date}` esiste già nella cache.
- Il rate limiting CoinGecko è gestito in `price_fetcher.py`: 1,2 sec/chiamata senza key, 0,3 sec/chiamata con Demo key. Non abbassare questi valori: il ban IP è silenzioso.
- `pd.ExcelWriter` + `openpyxl` per file grandi è lento. Per report con >500 righe valuta `xlsxwriter` che è 5-10× più veloce.
- Evita `.iterrows()` su DataFrame grandi. Se aggiungi logica batch, usa operazioni vettoriali o `.apply()` con `axis=1`.

---

## Normativa fiscale implementata

Fonte: L.197/2022, L.207/2024, circolari ADE.

| Anno | Aliquota | Franchigia | IVACA | Note |
|------|----------|------------|-------|------|
| ≤2022 | 26% | €51.646 | No | Vecchio regime valute estere |
| 2023–2024 | 26% | €2.000 | 0,2% | Prima applicazione L.197/2022 |
| 2025 | 26% | Abolita | 0,2% | L.207/2024 |
| 2026+ | 33% | Abolita | 0,2% | Default per anni futuri |

**Regole invarianti da non rompere mai:**
- Metodo **LIFO** obbligatorio in Italia: gli ultimi lotti acquistati sono i primi venduti.
- Il Quadro RW va compilato anche **senza vendite**, se si detiene al 31/12.
- Coinbase è intermediario **non residente**: l'obbligo RW si applica sempre (non derogabile).
- `SELL` e `CONVERT` sono entrambi eventi tassabili nel Quadro RT.
- `SEND`/`RECEIVE` tra wallet personali sono **neutri** solo se dimostrabile la titolarità.
- `Staking Income` / `Rewards Income` → crea un nuovo lotto al valore di mercato alla ricezione.
- La franchigia funziona come soglia: se netto < franchigia → imposta = 0 (non deduzione parziale).
- IVACA non dovuta se importo per singolo asset < €12.

---

## Formato CSV Coinbase (europeo)

```
riga 0: "Transactions"
riga 1: "User,Nome,UUID"
riga 2: header colonne   ← skiprows=3
riga 3+: dati
```

Colonne rilevanti: `ID`, `Timestamp`, `Transaction Type`, `Asset`,
`Quantity Transacted`, `Price Currency`, `Price at Transaction`,
`Subtotal`, `Total (inclusive of fees and/or spread)`,
`Fees and/or Spread`, `Notes`, `Sender Address`, `Recipient Address`.

Dopo la normalizzazione in `csv_loader.py`:

| Colonna normalizzata | Tipo | Descrizione |
|---------------------|------|-------------|
| `timestamp` | datetime (UTC, tz-aware) | Data/ora transazione |
| `date` | datetime.date | Solo data (tz-naive, sicuro per Excel) |
| `tx_type` | str | BUY/SELL/CONVERT/RECEIVE/SEND/STAKING/EARN/NEUTRAL/OTHER |
| `asset` | str | Ticker (es. BTC) |
| `quantity` | float | Quantità crypto |
| `price_currency` | str | EUR o USD |
| `price_orig` | float | Prezzo unitario (pulito da € / $) |
| `subtotal_orig` | float | Importo netto (senza fee) |
| `total_orig` | float | Importo totale (con fee) → usato come costo di acquisto |
| `fees_orig` | float | Fee |

**Attenzione**: `timestamp` è tz-aware (UTC). Non scriverlo mai direttamente in Excel (`ValueError: timezone-aware`). Usa sempre `date` o `timestamp.dt.tz_localize(None)`.

---

## Tipi di transazione mappati

```python
# csv_loader.TRANSACTION_TYPES (22 voci)
"buy"                          → BUY
"sell"                         → SELL
"convert"                      → CONVERT
"receive" / "deposit"          → RECEIVE
"send" / "withdrawal"          → SEND
"staking income" / "rewards income" / "inflation reward" → STAKING
"learning reward" / "coinbase earn" → EARN
"retail staking transfer" / "retail unstaking transfer"
  / "asset migration" / "retail eth2 deprecation"
  / "subscription" / "eth2 deposit" → NEUTRAL
```

Se arrivano nuovi tipi non mappati → `OTHER`. L'app mostra un warning.  
Quando aggiungi nuovi tipi, aggiornare `TRANSACTION_TYPES` in `csv_loader.py`.

---

## CoinGecko — ticker mappati

43 ticker mappati in `price_fetcher.TICKER_TO_ID`.  
Endpoint usato: `GET /api/v3/coins/{id}/history?date={DD-MM-YYYY}&localization=false`  
Risposta rilevante: `market_data.current_price.eur`

Per aggiungere un nuovo ticker:
1. Cerca il coin ID su [coingecko.com](https://www.coingecko.com) (URL: `/en/coins/{id}`)
2. Aggiungi `"TICKER": "coingecko-id"` in `TICKER_TO_ID`
3. Testa con `get_price_eur("TICKER", date(2025, 12, 31))`

Se CoinGecko non ha dati storici per un asset (risponde senza `market_data`), il fallback è l'ultima transazione nel CSV. Non rompere mai questo fallback.

---

## Session state Streamlit

| Chiave | Tipo | Quando viene settata |
|--------|------|----------------------|
| `df` | DataFrame | Dopo upload CSV |
| `uploaded_filename` | str | Dopo upload CSV |
| `available_years` | list[int] | Dopo upload CSV |
| `rates` | dict | Dopo fetch BCE |
| `market_prices_{year}` | dict | Dopo fetch CoinGecko per quell'anno |

Il selettore anno legge `available_years` da session_state. Se non presente → default `[TAX_YEAR]`.  
I prezzi CoinGecko sono separati per anno: cambiare anno non invalida i prezzi dell'anno precedente.

---

## Excel output (formato standard)

Il file Excel RW generato da `excel_report.generate_rw_excel()` deve avere sempre:

**Foglio "Riassunto"** — colonne nell'ordine:
1. Etichetta
2. Controvalore inizio detenzione
3. Data Inizio detenzione (`01-01-YYYY`)
4. Valore Iniziale RW (intero arrotondato)
5. Controvalore fine detenzione
6. Data ultimo giorno detenzione (`31-12-YYYY`)
7. Valore Finale RW (intero arrotondato)
8. 0,2% Del Valore Finale RW
9. Giorni detenzione
10. IC rapportato ai giorni di detenzione

**Foglio "Coinbase"** — stesse colonne ma con dettaglio per asset (Simbolo, Quantità ×2, Prezzo ×2).

Riga "Complessivo" sempre in fondo, con totali. Styling: header blu scuro, righe alternate azzurro/bianco, totale blu medio.

---

## Cosa manca / possibili evoluzioni

- [ ] Supporto wallet personali (Ledger, MetaMask) — richiedono CSV separati e rigo RW distinto
- [ ] Supporto multi-exchange (Binance, Kraken, ecc.) — aggiungere loader specifici in `csv_loader.py`
- [ ] Calcolo RT per Staking/EARN — oggi creano lotti ma non generano RT separato
- [ ] Export PDF della scheda di compilazione
- [ ] Test automatici (`pytest`) sui moduli di calcolo fiscale
- [ ] Inserimento manuale prezzi al 01/01 e 31/12 come override rispetto a CoinGecko
- [ ] Gestione conversioni fiat (es. vendita crypto → EUR su Coinbase)
- [ ] `@st.cache_data` su `compute_rw_data` e `compute_rt_data` per performance

---

## Comandi utili

```bash
# Avvia la dashboard
streamlit run app.py

# Genera report da CLI (richiede data/coinbase_export.csv)
python main.py

# Verifica sintassi senza avviare
python3 -m py_compile app.py modules/*.py

# Svuota cache prezzi CoinGecko (utile se i dati sembrano sbagliati)
rm data/price_cache.json

# Svuota cache tassi BCE
rm data/exchange_rates.csv

# Reinstalla dipendenze
pip install -r requirements.txt
```

---

## .gitignore consigliato

```gitignore
.env
data/
output/
__pycache__/
*.pyc
*.xlsx
~$*
.DS_Store
```

Non committare mai: `.env` (API key), `data/*.csv` (dati fiscali personali), `data/*.json` (cache con dati di mercato).
