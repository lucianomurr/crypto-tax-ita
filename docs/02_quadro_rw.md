# Quadro RW – Monitoraggio Fiscale e IVACA

> Fonte: Circolare ADE n. 30/E del 27/10/2023, § 3.4

---

## Finalità

Il Quadro RW è obbligatorio per le persone fisiche residenti in Italia che detengono cripto-attività, **indipendentemente dalle modalità di archiviazione** e dal fatto che siano detenute in Italia o all'estero.

Va compilato anche se il contribuente ha **totalmente disinvestito** nel corso del periodo d'imposta.

Ha due funzioni:
1. Monitoraggio fiscale (comunicare il possesso all'Agenzia delle Entrate)
2. Calcolo e versamento dell'IVACA (imposta sostitutiva dell'imposta di bollo, anche chiamata "IC")

---

## Compilazione semplificata — UN RIGO PER ACCOUNT

La Circolare ADE n. 30/E del 27/10/2023 (§ 3.4) consente una **compilazione semplificata**:

> Si può compilare **un unico rigo** per ogni "portafoglio" o "conto digitale" o altro sistema di archiviazione o conservazione, indicando il valore **cumulativo** di tutte le cripto-attività al suo interno.

**Per chi usa solo Coinbase: un solo rigo per tutto il conto Coinbase.**

**Obbligo accessorio**: predisporre e conservare un **prospetto analitico** separato con i valori delle singole cripto-attività, da esibire in caso di verifica fiscale. L'app genera questo prospetto nel file Excel (foglio "Coinbase").

In alternativa, è facoltà del contribuente compilare un rigo per ciascuna singola cripto-attività (confermato dall'ADE nella Videoconferenza del 01/02/2024).

---

## Campi da compilare (Modello Redditi PF)

| Colonna | Nome | Valore per Coinbase | Note |
|---------|------|---------------------|------|
| **1** | Titolo di possesso | `1` | Proprietà diretta |
| **3** | Codice individuazione bene | `21` | Cripto-attività |
| **4** | Codice Stato estero | **VUOTO** | Le cripto-attività non hanno localizzazione geografica |
| **5** | Quota di possesso (%) | `100` | Se proprietà esclusiva; altro valore se cointestate |
| **6** | Criterio determinazione valore | `1` | Valore di mercato |
| **7** | Valore iniziale | Valore totale portafoglio al 01/01 (€) | |
| **8** | Valore finale | Valore totale portafoglio al 31/12 (€) | Arrotondare all'euro |
| **10** | Giorni IC | Giorni di detenzione nell'anno | Vedi sezione sotto |
| **14** | Codice quadro reddituale | `3` | Se compili solo Quadro RT |
| **16** | Flag imposta di bollo pagata | Non spuntare | Coinbase non paga per l'utente |
| **33** | IC calcolata | Valore finale × 0,002 × (giorni/365) | |
| **34** | IC dovuta | = col. 33 se ≥ € 12, altrimenti 0 | |

> Per il **Modello 730** i campi corrispondono alle stesse colonne del Riquadro **W**, con la stessa logica di compilazione.

### Colonna 14 — Codice quadro reddituale

| Codice | Quando usarlo |
|--------|---------------|
| `1` | Compili solo Quadro RL |
| `2` | Compili solo Quadro RM |
| `3` | Compili solo Quadro RT (caso più comune per crypto) |
| `4` | Compili due o tre quadri tra RL, RM, RT |
| `5` | Asset infruttiferi o redditi percepibili in periodo successivo |

### RW8 — Imposta cripto-attività

Il rigo **RW8** deve essere compilato per il totale IVACA. Se si usano più moduli RW, compilare RW8 **solo nel primo modulo** indicando il totale complessivo.

- **RW8 colonna 4** (acconti versati): eventuali acconti IVACA versati l'anno precedente

---

## Calcolo IVACA (IC)

```
IC = Valore finale (€) × 0,002 × (giorni detenzione / 365)
```

- **IC dovuta** se IC ≥ € 12, altrimenti non è dovuta
- Versamento tramite **F24 con codice tributo `1717`**

**Esempio:**
```
Portafoglio Coinbase al 31/12:  € 9.500
Giorni detenzione:              365
IC = 9.500 × 0,002 × (365/365) = € 19,00
→ Dovuta (≥ € 12) → versare € 19 con F24 codice 1717
```

**Esempio sotto soglia:**
```
Portafoglio Coinbase al 31/12:  € 4.000
IC = 4.000 × 0,002 = € 8,00
→ Non dovuta (< € 12) → inserire 0 in colonna 34
```

---

## Periodo di detenzione

Il periodo di detenzione per il Quadro RW è **unico** per tutto l'account:
- **Inizia** quando la prima cripto-attività entra nel conto
- **Termina** quando il conto viene completamente svuotato
- Acquisti e vendite intermedie **non interrompono** il periodo di detenzione

Per chi usa Coinbase da anni e ha ancora saldo: giorni = **365** (tutto l'anno).

---

## Valore di mercato al 01/01 e al 31/12

Il valore deve essere il **prezzo di mercato reale** alla data esatta.

Fonti accettate dall'ADE (Circolare 30/E del 27/10/2023):
- Prezzo indicato sulla piattaforma dove il contribuente ha acquistato (es. Coinbase)
- Piattaforme analoghe dove le stesse cripto-attività sono negoziabili
- Siti specializzati nella rilevazione dei valori di mercato (es. CoinGecko, CoinMarketCap)

> L'app scarica automaticamente i prezzi storici da **CoinGecko** tramite il pulsante "Scarica prezzi storici" nella sidebar.

---

## Commissioni (fee) — importante distinzione

A differenza degli strumenti finanziari tradizionali (dove le commissioni aumentano il costo fiscale, art. 68 comma 6 TUIR), per le **cripto-attività** il **comma 9-bis** del TUIR stabilisce che:

> Non si tiene conto dei costi inerenti l'acquisto e la cessione nella determinazione dei redditi diversi derivanti dalle cripto-attività.

In pratica: le fee pagate a Coinbase **non sono deducibili** ai fini fiscali.

> ⚠️ Questa disposizione riguarda principalmente la deducibilità delle fee come costo separato nel Quadro RT. Consultare un commercialista per l'applicazione specifica al proprio caso.

---

## Prospetto analitico (da conservare)

Con la compilazione semplificata (un rigo per account), è **obbligatorio** conservare un prospetto con i valori per singola cripto-attività, da produrre in caso di verifica fiscale.

Il file Excel generato dall'app (foglio "Coinbase") costituisce questo prospetto e contiene per ogni asset:
- Simbolo
- Quantità al 01/01 e al 31/12
- Prezzo alla data (01/01 e 31/12)
- Valore al 01/01 e al 31/12
- IVACA calcolata e proratizzata per i giorni di detenzione
