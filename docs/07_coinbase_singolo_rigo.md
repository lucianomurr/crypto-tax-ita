# Guida Compilazione — Singolo Rigo Coinbase

> Istruzioni per chi ha il portafoglio crypto interamente su Coinbase.  
> Basata sulla compilazione semplificata prevista dalla Circolare ADE n. 30/E del 27/10/2023 (§ 3.4).  
> ⚠️ Verificare sempre i valori con un commercialista prima di presentare la dichiarazione.

---

## Principio: un solo rigo per tutto Coinbase

Con la compilazione semplificata dell'ADE, tutto il portafoglio Coinbase va dichiarato in **un unico rigo** del Quadro RW (o Riquadro W del 730), indicando il valore **complessivo** di tutte le cripto-attività.

Il dettaglio per singolo asset viene conservato nel prospetto analitico (file Excel generato dall'app, foglio "Coinbase").

---

## Come trovare i valori nell'app

Tutti i valori da inserire nel modulo si trovano nel tab **📝 Compila Dichiarazione** dell'app:

1. Carica il CSV Coinbase dalla sidebar
2. Seleziona l'anno d'imposta
3. Clicca **"Scarica prezzi storici"** per ottenere prezzi reali al 01/01 e 31/12
4. Il tab "Compila Dichiarazione" mostra i valori precompilati per ogni campo

---

## Quadro RW (Modello Redditi PF) / Riquadro W (Modello 730)

Compila **un solo rigo** con questi valori:

| Colonna | Nome campo | Valore da inserire | Dove trovarlo |
|---------|-----------|-------------------|---------------|
| **1** | Titolo di possesso | `1` | Fisso |
| **3** | Codice individuazione bene | `21` | Fisso (cripto-attività) |
| **4** | Codice Stato estero | *(lasciare vuoto)* | Fisso |
| **5** | Quota di possesso (%) | `100` | Fisso (se proprietà esclusiva) |
| **6** | Criterio determinazione valore | `1` | Fisso (valore di mercato) |
| **7** | Valore iniziale al 01/01 | `[valore totale portafoglio 01/01]` | App → tab Quadro RW → colonna "Valore Iniziale" → somma |
| **8** | Valore finale al 31/12 | `[valore totale portafoglio 31/12]` | App → tab Quadro RW → colonna "Valore Finale" → somma |
| **10** | Giorni IC | `[giorni detenzione]` | 365 se hai avuto saldo per tutto l'anno |
| **14** | Codice quadro reddituale | `3` | Se compili solo Quadro RT; vedi tabella sotto |
| **16** | Flag imposta di bollo pagata | *(non spuntare)* | Coinbase non paga per l'utente |
| **33** | IC calcolata | `[col.8 × 0,002 × giorni/365]` | App → tab Quadro RW → colonna "IVACA Calcolata" → somma |
| **34** | IC dovuta | `[IC se ≥ €12, altrimenti 0]` | App → tab Quadro RW → colonna "IVACA Dovuta" → somma |

### Colonna 14 — quale codice usare

| Situazione | Codice |
|---|---|
| Compili solo Quadro RT | `3` |
| Compili Quadro RT + Quadro RL | `4` |
| Compili Quadro RT + Quadro RM | `4` |
| Asset infruttiferi senza altri quadri | `5` |

### RW8 — Imposta cripto-attività (totale IVACA)

- **RW8 totale IC**: inserire la somma di tutte le IC (= valore colonna 34 del rigo)
- **RW8 colonna 4 (acconti versati)**: acconti IVACA già versati l'anno precedente (codice `1717`)
- Se RW8 totale < € 12: **nessun versamento dovuto**

---

## Quadro RT (Modello Redditi PF) / Riquadro T (Modello 730)

Da compilare solo se hai avuto vendite o conversioni nell'anno.

| Campo RT | Campo T | Descrizione | Dove trovarlo |
|----------|---------|-------------|---------------|
| **RT41 col. 1** | T41 col. 1 | Totale corrispettivi (ricavi) | App → tab Compila Dichiarazione → RT23 |
| **RT41 col. 2** | T41 col. 2 | Totale costi di acquisto LIFO | App → tab Compila Dichiarazione → RT24 |
| **RT57 col. 2** | T57 col. 2 | Plusvalenze nette | App → tab Compila Dichiarazione → RT25 |
| **RT57 col. 1** | T57 col. 1 | Minusvalenze nette | App → tab Compila Dichiarazione → RT26 |
| **RT43** | T43 | Minusvalenze anni precedenti (dal 2023) | Tua dichiarazione anno precedente → RT105 |
| **RT88** | — | Base imponibile (RT57 col.2 − RT43) | Calcolo manuale |
| **RT89** | — | Imposta sostitutiva (26%) | RT88 × 0,26 |
| **RT90** | — | Totale imposta dovuta | = RT89 |

---

## Esempio con valori fittizi

Per un portafoglio ipotetico con:
- Valore totale al 01/01: **€ 12.000**
- Valore totale al 31/12: **€ 9.500**
- Vendite nell'anno: plusvalenza netta **€ 800**
- Giorni detenzione: **365**

**Quadro RW:**

| Campo | Valore |
|---|---|
| Col. 7 – Valore iniziale | `12000` |
| Col. 8 – Valore finale | `9500` |
| Col. 10 – Giorni IC | `365` |
| Col. 33 – IC calcolata | `19` (= 9.500 × 0,002) |
| Col. 34 – IC dovuta | `19` (≥ € 12 → dovuta) |

**Quadro RT (anno 2025, franchigia abolita):**

| Campo | Valore |
|---|---|
| RT41 col. 1 | `3.500` (ricavi totali) |
| RT41 col. 2 | `2.700` (costi LIFO) |
| RT57 col. 2 | `800` (plusvalenza netta) |
| RT88 | `800` |
| RT89 (26%) | `208` |
| RT90 | `208` |

**F24:**

| Imposta | Codice | Importo |
|---|---|---|
| IVACA saldo | `1717` | `€ 19` |
| Plusvalenze saldo | `1716` | `€ 208` |

---

## Prospetto analitico da conservare

Con la compilazione a rigo unico, devi conservare il dettaglio per singolo asset. L'app genera questo prospetto automaticamente:

1. Vai nel tab **🏦 Quadro RW** dell'app
2. Clicca **⬇️ Report RW (Excel)**
3. Il foglio "Coinbase" contiene il prospetto analitico con tutti gli asset, quantità e valori

**Conserva questo file per almeno 5 anni** insieme al CSV originale di Coinbase.

---

## Determinazione dei giorni di detenzione

| Situazione | Giorni |
|---|---|
| Hai avuto saldo per tutto l'anno (01/01 → 31/12) | `365` |
| Hai aperto il conto durante l'anno | Dal giorno del primo deposito al 31/12 |
| Hai azzerato il conto durante l'anno | Dal 01/01 all'ultimo giorno di detenzione |
| Hai aperto e chiuso il conto nello stesso anno | Dal primo deposito all'ultimo prelievo |

Il periodo di detenzione su Coinbase è **unico** per tutto l'account: acquisti e vendite intermedie non lo interrompono.
