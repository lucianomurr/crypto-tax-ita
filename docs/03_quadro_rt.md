# Quadro RT – Plusvalenze e Minusvalenze

> Sezione V-A del Quadro RT (Modello Redditi PF) / Quadro T (Modello 730)  
> Riferimento: art. 67 comma 1 lett. c-sexies TUIR; Circolare ADE n. 30/E del 27/10/2023

---

## Quando si compila

Il Quadro RT va compilato se nell'anno d'imposta si sono effettuate:
- **Vendite** (cessione a titolo oneroso di cripto-attività per valuta FIAT)
- **Conversioni** (permuta di cripto-attività con caratteristiche diverse)
- **Rimborsi** di cripto-attività
- **Proventi da detenzione** (staking, earn — se fiscalmente rilevanti)

Dalla vendita può derivare:
- **Plusvalenza**: corrispettivo > costo di acquisto → imposta sostitutiva del 26% (33% dal 2026)
- **Minusvalenza**: corrispettivo < costo di acquisto → deducibile per 4 anni successivi

---

## Metodo LIFO (obbligatorio in Italia)

Il metodo **LIFO (Last In, First Out)** è prescritto dalle autorità fiscali italiane: quando si vende, si considera venduto prima **l'ultimo lotto acquistato**.

### Esempio

```
Acquisto 1:  0,3 BTC a 20.000 €  (gennaio 2025)
Acquisto 2:  0,2 BTC a 25.000 €  (marzo 2025)
Vendita:     0,2 BTC a 30.000 €  (settembre 2025)

Con LIFO → si considera venduto l'Acquisto 2 (l'ultimo):
  Costo fiscale:   25.000 €
  Prezzo vendita:  30.000 €
  Plusvalenza:      5.000 €
  Imposta (26%):    1.300 €
```

> ⚠️ Caricare sempre il CSV con **tutta la cronologia storica**: i lotti di anni precedenti determinano il costo di carico delle vendite dell'anno corrente.

---

## Formula plusvalenza

```
Plusvalenza = Corrispettivo percepito − Costo o valore di acquisto (LIFO)
```

**Corrispettivo**: il prezzo di vendita effettivamente ricevuto (valore normale in caso di permuta).  
**Costo di acquisto**: il prezzo pagato per l'acquisizione dei lotti LIFO corrispondenti.

### Commissioni (fee) — art. 68 comma 9-bis TUIR

Per le cripto-attività, a differenza degli strumenti finanziari tradizionali, **le fee non concorrono** alla determinazione del costo di acquisto né del corrispettivo ai fini del calcolo delle plusvalenze/minusvalenze.

> ⚠️ L'applicazione pratica di questa norma è dibattuta. Verificare con un commercialista la modalità corretta per il proprio caso specifico.

---

## Franchigia (anni 2023–2024) e abolizione (2025+)

| Anno | Franchigia | Modalità |
|------|-----------|---------|
| 2023–2024 | **€ 2.000** | Se reddito netto ≤ €2.000: imposta = 0 |
| 2025+ | **Abolita** | Qualsiasi plusvalenza netta è imponibile |

> La franchigia è una **soglia**: se il guadagno netto supera €2.000, l'imposta è dovuta sull'intero importo eccedente la soglia (non sull'intero guadagno netto). Verificare con un commercialista l'interpretazione applicabile.

---

## Campi del Quadro RT (Modello Redditi PF)

### Sezione V-A

| Campo | Descrizione | Da inserire |
|-------|-------------|-------------|
| **RT41 col. 1** | Totale corrispettivi | Somma di tutti i ricavi delle vendite/permute/rimborsi |
| **RT41 col. 2** | Totale costi di acquisto | Somma dei costi LIFO corrispondenti |
| **RT42 col. 1** | Costo rideterminato (col. 1) | Solo se si è effettuata la rivalutazione |
| **RT42 col. 2** | Costo rideterminato (col. 2) | Solo se si è effettuata la rivalutazione |
| **RT43** | Eccedenza minusvalenze anni precedenti | Minusvalenze da anni precedenti (dal 2023 in poi) |
| **RT44** | Eccedenza minusvalenze da intermediari | Minusvalenze certificate da intermediari finanziari |
| **RT45** | Eccedenza imposta sostitutiva precedente | Credito da dichiarazione precedente |

> ⚠️ Le minusvalenze crypto antecedenti al 2023 **non si possono compensare** con plusvalenze crypto post 2023.

### Sezione VI

| Campo | Descrizione | Formula |
|-------|-------------|---------|
| **RT57 col. 1** | Minusvalenze | RT41 − RT42, se negativo e > €2.000 |
| **RT57 col. 2** | Plusvalenze nette | RT41 − RT42, se positivo e > €2.000 |

### Sezione V-B

| Campo | Descrizione | Formula |
|-------|-------------|---------|
| **RT88** | Base imponibile netta | RT57 col.2 − RT43 − RT44 col.2 |
| **RT89** | Imposta sostitutiva | RT88 × 26% |
| **RT90** | Totale imposta sostitutiva dovuta | Imposta da pagare |
| **RT105 Sez. V** | Quote residue minusvalenze | Minusvalenze residue da riportare agli anni successivi |

---

## Campi del Quadro T (Modello 730)

La struttura è identica al Quadro RT, con i campi rinominati:

| Quadro RT | Quadro T | Descrizione |
|-----------|----------|-------------|
| RT41 | T41 | Corrispettivi / costi |
| RT42 | T42 | Costo rideterminato |
| RT43 | T43 | Eccedenza minusvalenze anni precedenti |
| RT44 | T44 | Eccedenza minusvalenze da intermediari |
| RT45 | T45 | Eccedenza imposta precedente |
| RT57 | T57 | Minusvalenze / plusvalenze |
| RT105 Sez. V | RT105 Sez. V | Quote residue minusvalenze |

---

## Conversione in euro

Le transazioni in valuta estera (USD) devono essere convertite in euro al **tasso di cambio BCE del giorno della transazione**.

- Per weekend e festivi: tasso del giorno lavorativo precedente
- Fonte: [Banca Centrale Europea](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/)
- I CSV Coinbase europei hanno i prezzi già in **EUR** → nessuna conversione necessaria

---

## Compensazione minusvalenze

1. **Stesso anno**: minusvalenze riducono le plusvalenze dell'anno corrente
2. **Anni successivi**: eccedenza non compensata deducibile nei **4 anni successivi**

**Condizione**: la minusvalenza deve essere **dichiarata nell'anno in cui si verifica**, anche senza plusvalenze da compensare.

> ⚠️ Le minusvalenze crypto realizzate **prima del 2023** non sono compensabili con plusvalenze crypto post 2023.
