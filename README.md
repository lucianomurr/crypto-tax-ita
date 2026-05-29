# Crypto Tax IT

![CI](https://github.com/{username}/{repo}/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red.svg)
![Tests](https://img.shields.io/badge/tests-70%20passed-brightgreen.svg)

Dashboard per la dichiarazione fiscale italiana delle cripto-attività.  
Calcola automaticamente i dati per i **Quadri RT e RW** (o Riquadri T e W del 730) partendo dal CSV esportato da Coinbase.

---

## ⚠️ Disclaimer

**Questo strumento è fornito esclusivamente a scopo informativo ed educativo.**

- Non costituisce consulenza fiscale, legale o finanziaria di alcun tipo
- I calcoli prodotti potrebbero essere incompleti, imprecisi o non applicabili alla tua situazione specifica
- Le normative fiscali sulle cripto-attività sono soggette a frequenti aggiornamenti
- I risultati non sostituiscono in alcun modo il parere di un commercialista o consulente tributario abilitato

**Prima di presentare qualsiasi dichiarazione fiscale è obbligatorio:**
1. Verificare in modo indipendente tutti i dati e i calcoli
2. Consultare un professionista fiscale qualificato (commercialista)
3. Incrociare i risultati con le fonti ufficiali dell'Agenzia delle Entrate

Gli autori e i contributori di questo software non si assumono alcuna responsabilità per perdite, sanzioni, multe o danni derivanti dall'uso o dall'affidamento a questo software o ai suoi output.

---

## Requisiti

- Python 3.10+
- Connessione internet (per i tassi BCE e i prezzi CoinGecko)

---

## Installazione

```bash
# Clona o scarica il progetto
cd crypto-tax

# Installa le dipendenze
pip install -r requirements.txt
```

---

## Configurazione

### 1. File `.env` (opzionale ma consigliato)

Crea o modifica il file `.env` nella root del progetto:

```env
COINGECKO_API_KEY=CG-xxxxxxxxxxxxxxxxxxxx
```

La **Demo API key è gratuita**: registrati su [coingecko.com](https://www.coingecko.com) → Developers → My API Keys.  
Senza key l'app funziona comunque, ma il recupero dei prezzi storici è più lento (~1 sec per asset invece di ~0,3 sec).

### 2. CSV Coinbase

Scarica la cronologia delle transazioni da Coinbase:

1. Accedi a [coinbase.com](https://www.coinbase.com)
2. Menu → **Strumenti → Rapporti**
3. Clicca **+ Nuovo Rapporto**
4. Seleziona: Tipo → **Cronologia delle transazioni** | Intervallo → **Tutta la cronologia**
5. Crea il rapporto e scarica il CSV quando ricevi la notifica via email

> Scarica la cronologia **completa** (non solo l'anno corrente): i lotti di acquisto degli anni precedenti servono per il calcolo LIFO corretto.

---

## Avvio

```bash
streamlit run app.py
```

La dashboard si apre automaticamente su [http://localhost:8501](http://localhost:8501).

---

## Utilizzo

### Passo 1 — Carica il CSV

Nella **sidebar sinistra**, clicca su "📂 Carica CSV Coinbase" e seleziona il file scaricato da Coinbase.  
L'app rileva automaticamente tutti gli anni presenti nella cronologia.

### Passo 2 — Seleziona l'anno d'imposta

Usa il selettore **"📅 Anno d'imposta"** per scegliere l'anno da dichiarare (es. 2025).  
I parametri fiscali si aggiornano automaticamente:

| Anno | Aliquota | Franchigia | IVACA |
|------|----------|------------|-------|
| 2020–2022 | 26% | € 51.646 | Non prevista |
| 2023–2024 | 26% | € 2.000 | 0,2% |
| 2025 | 26% | Abolita | 0,2% |
| 2026+ | 33% | Abolita | 0,2% |

### Passo 3 — Scarica i prezzi storici (per valori RW precisi)

Clicca **"Scarica prezzi storici"** nella sidebar per ottenere i prezzi di mercato reali al 01/01 e 31/12 da CoinGecko.  
I prezzi vengono salvati in `data/price_cache.json` e riutilizzati nelle sessioni successive.

> Senza questo passo, il valore degli asset nel Quadro RW viene approssimato con il prezzo dell'ultima transazione disponibile nel CSV — meno preciso.

### Passo 4 — Consulta i risultati

La dashboard è organizzata in **5 tab**:

| Tab | Contenuto |
|-----|-----------|
| **📊 Overview** | KPI fiscali, grafico portfolio, volume transazioni, totale acquisti, totale vendite e differenza netta |
| **📝 Compila Dichiarazione** | Valori pronti da copiare nel Modello 730 (Riquadri W e T) o Redditi PF (Quadri RW e RT), con istruzioni campo per campo e codici F24 |
| **🏦 Quadro RW** | Dettaglio asset per il monitoraggio fiscale: quantità, valore iniziale/finale, IVACA calcolata e dovuta |
| **📈 Quadro RT** | Plusvalenze e minusvalenze LIFO, imposta dovuta, grafici per operazione e per asset |
| **🔢 Dettaglio LIFO** | Saldo inventario LIFO e dettaglio costo di carico per ogni operazione di vendita |
| **📋 Transazioni** | Storico completo con filtri per asset, tipo e anno |

### Passo 5 — Scarica i report

Ogni tab offre pulsanti di download:

- **Report RW (Excel – formato standard)**: foglio "Riassunto" + foglio "Coinbase" con struttura compatibile con i software di dichiarazione
- **Report RT (CSV)**: dettaglio operazioni LIFO pronto per il commercialista
- **Scheda Compilazione (Excel)**: valori precompilati per ogni campo del modulo fiscale
- **Report completo (Excel)**: tutte le transazioni + quadri RT e RW in un unico file

---

## Struttura del progetto

```
crypto-tax/
├── app.py                  # Dashboard Streamlit (entry point principale)
├── main.py                 # Alternativa CLI (senza interfaccia grafica)
├── config.py               # Parametri fiscali per anno (aliquote, franchigie, IVACA)
├── requirements.txt
├── .env                    # API key CoinGecko (non committare su git)
│
├── modules/
│   ├── csv_loader.py       # Parsing CSV Coinbase (formato EU e US)
│   ├── exchange_rates.py   # Tassi BCE EUR/USD con cache locale
│   ├── lifo_engine.py      # Motore di calcolo LIFO
│   ├── price_fetcher.py    # Prezzi storici da CoinGecko con cache
│   ├── rw_report.py        # Calcolo Quadro RW e IVACA
│   ├── rt_report.py        # Calcolo Quadro RT e plusvalenze
│   └── excel_report.py     # Generazione Excel formato standard
│
├── data/
│   ├── coinbase_export.csv     # Il tuo CSV Coinbase (non committare su git)
│   ├── exchange_rates.csv      # Cache tassi BCE (auto-generato)
│   └── price_cache.json        # Cache prezzi CoinGecko (auto-generato)
│
└── output/                 # Report generati dal CLI
```

---

## Utilizzo da CLI (senza interfaccia grafica)

In alternativa alla dashboard, puoi usare il terminale:

```bash
# Posiziona il CSV in data/coinbase_export.csv
python main.py
```

I report vengono salvati in `output/report_RW_2025.csv` e `output/report_RT_2025.csv`.

---

## Sviluppo & Test

```bash
# Installa dipendenze di sviluppo
pip install -r requirements-dev.txt

# Esegui tutti i test (70 test)
pytest tests/ -v

# Test con copertura del codice
pytest tests/ --cov=modules --cov=config --cov-report=term-missing

# Verifica sintassi
python -m py_compile app.py modules/*.py

# Svuota cache CoinGecko (se i prezzi sembrano sbagliati)
rm data/price_cache.json
```

La CI esegue i test automaticamente su Python 3.10, 3.11 e 3.12 ad ogni push. Vedi `.github/workflows/ci.yml`.

---

## Note fiscali importanti

### Metodo LIFO
L'Italia richiede il metodo **LIFO (Last In, First Out)**: quando vendi, si considera venduto prima l'ultimo lotto acquistato. Per questo è essenziale caricare la **cronologia completa** delle transazioni, anche degli anni precedenti.

### Quadro RW — quando va compilato
Obbligatorio per tutti i residenti fiscali italiani che detengono cripto-attività al 31 dicembre, **anche in assenza di vendite**. Coinbase è un intermediario non residente in Italia, quindi l'obbligo RW si applica sempre.

### Quadro RT — quando va compilato
Solo se nell'anno sono state effettuate **vendite o conversioni** di cripto-attività.

### Valore al 31/12 per il Quadro RW
Il valore dei beni dichiarati nel Quadro RW deve corrispondere al **prezzo di mercato al 31 dicembre**. Usa il pulsante "Scarica prezzi storici" per ottenere i valori reali da CoinGecko, oppure inserisci manualmente i prezzi dal sito della borsa valori di riferimento.

### Transazioni non classificate
Se l'app segnala transazioni "OTHER" (non classificate), verificale manualmente: potrebbero essere tipi di operazione non ancora mappati (es. airdrops, liquidazioni).

### Wallet personali esterni
I wallet personali (Ledger, MetaMask, ecc.) richiedono un **rigo RW separato** per ciascuno e non vengono gestiti automaticamente da questa app.

---

## Scadenze 2026 (per redditi 2025)

| Adempimento | Scadenza | Codice tributo F24 |
|-------------|----------|--------------------|
| Acconto IVACA | 30 novembre 2025 | 1717 |
| Saldo IVACA | 30 giugno 2026 | 1717 |
| Imposta plusvalenze | 30 giugno 2026 | 1715 (acconto) / 1716 (saldo) |
| Modello 730 | 30 settembre 2026 | — |
| Modello Redditi PF | 15 ottobre 2026 | — |

---

## Riferimenti normativi

- Legge n. 197/2022 (Legge di Bilancio 2023) — introduzione regime fiscale cripto
- Legge n. 207/2024 (Legge di Bilancio 2025) — abolizione franchigia, conferma aliquota 26%
- Circolare ADE n. 30/E del 2023 — chiarimenti operativi

---

## Licenza

Distribuito sotto licenza **MIT**. Vedi il file [LICENSE](LICENSE) per i dettagli completi.

Il testo della licenza include un'avvertenza esplicita sull'uso del software in ambito fiscale: i risultati prodotti non costituiscono consulenza professionale e l'utilizzo è a proprio rischio.
