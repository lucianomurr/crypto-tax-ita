# Tipi di Transazione – Rilevanza Fiscale

> Fonte: Circolare ADE n. 30/E del 27/10/2023; art. 67 comma 1 lett. c-sexies TUIR

---

## Tabella di riferimento

| Tipo Coinbase | Codice app | RW | RT | Trattamento |
|---|---|:---:|:---:|---|
| Buy / Advanced Trade Buy | `BUY` | ✅ | ❌ | Acquisto: crea nuovo lotto LIFO |
| Sell / Advanced Trade Sell | `SELL` | ✅ | ✅ | Vendita: realizzo plusvalenza/minusvalenza LIFO |
| Convert / Simple Dust | `CONVERT` | ✅ | ✅ | Permuta: trattato come vendita + acquisto (evento tassabile) |
| Receive / Deposit | `RECEIVE` | ✅ | ❌ | Neutro se da wallet personale con prova titolarità |
| Send / Withdrawal | `SEND` | ✅ | ❌ | Neutro se verso wallet personale con prova titolarità |
| Staking Income / Rewards Income | `STAKING` | ✅ | ✅ | **Fiscalmente rilevante**: reddito al valore di mercato alla ricezione |
| Learning Reward / Coinbase Earn | `EARN` | ✅ | ✅ | **Fiscalmente rilevante**: reddito diverso |
| E-money Token | `EARN` | ✅ | ✅ | **Fiscalmente rilevante** |
| Retail Staking Transfer | `NEUTRAL` | ✅ | ❌ | Spostamento tecnico in staking: non tassabile |
| Retail Unstaking Transfer | `NEUTRAL` | ✅ | ❌ | Uscita tecnica dallo staking: non tassabile |
| Asset Migration / ETH2 Deprecation | `NEUTRAL` | ✅ | ❌ | Migrazione tecnica: non è cessione |
| Subscription | `NEUTRAL` | — | ❌ | Non rilevante |

---

## Rilevanza fiscale per tipo (parametri di calcolo)

| Tipo operazione | Fiscalmente rilevante per RT |
|---|:---:|
| Tipologia di calcolo | **LIFO** |
| Airdrop | **NO** |
| Mining | **NO** |
| Fork | **NO** |
| Cashback | **NO** |
| Earn / Learning Reward | **SÌ** |
| Staking | **SÌ** |
| E-money Token | **SÌ** |

> Fonte: parametri applicati dalla prassi professionale in conformità alla Circolare n. 30/E del 27/10/2023.

---

## Note per tipo

### BUY
- Crea un nuovo lotto LIFO con costo = prezzo pagato
- Le fee in linea teorica non aumentano il costo fiscale (art. 68 comma 9-bis TUIR, vedi nota sotto)

### SELL
- Vendita in valuta FIAT: evento tassabile nel Quadro RT
- Ricavo = corrispettivo percepito al netto delle fee (in linea teorica)

### CONVERT (Permuta)
- Scambio di una cripto-attività con un'altra = **due eventi fiscali**:
  1. Vendita della cripto ceduta al valore di mercato → RT
  2. Acquisto della cripto ricevuta al valore di mercato → nuovo lotto LIFO
- Genera plusvalenza/minusvalenza anche senza uscire in fiat

### STAKING / EARN
- Al momento della ricezione: il valore di mercato in € diventa il **costo del nuovo lotto LIFO**
- Sono anche **reddito imponibile** nell'anno di ricezione
- Nei periodi successivi, se venduti, generano plusvalenza/minusvalenza calcolata da quel costo

### RECEIVE / SEND tra wallet personali
- **Neutri** solo con prova di titolarità del wallet
- Non cambiano il costo di carico LIFO (il lotto mantiene il costo originale)
- Va sempre aggiunto un rigo RW separato per i wallet personali

### AIRDROP (non gestito automaticamente)
- **Non fiscalmente rilevante** al momento della ricezione secondo la prassi prevalente
- Il costo fiscale del lotto è tipicamente zero (o il valore al momento della ricezione — verificare con commercialista)
- Richiede analisi caso per caso

### FORK (non gestito automaticamente)
- **Non fiscalmente rilevante** al momento del fork
- Trattamento simile all'airdrop

---

## Nota sulle commissioni (fee)

L'art. 68, comma 9-bis del TUIR stabilisce che per le cripto-attività, a differenza degli strumenti finanziari tradizionali (dove il comma 6 consente di includere le commissioni nel costo), **non si tiene conto dei costi inerenti l'acquisto e la cessione** nella determinazione dei redditi diversi.

In pratica:
- **Strumenti finanziari tradizionali**: costo = prezzo + commissioni
- **Cripto-attività**: costo = prezzo senza commissioni (norma letterale)

> ⚠️ L'interpretazione pratica di questa norma è dibattuta nel settore. Alcuni professionisti ritengono che il prezzo pagato (comprensivo di fee incorporate nel prezzo) sia comunque il costo fiscale. Verificare con un commercialista la corretta applicazione al proprio caso.

---

## Casi speciali non gestiti dall'app

| Caso | Motivo | Azione richiesta |
|---|---|---|
| NFT | Normativa in evoluzione | Analisi manuale con commercialista |
| Token DeFi (lending, liquidity pool) | Protocolli complessi | Analisi manuale |
| Airdrops | Trattamento fiscale da definire | Verificare con commercialista |
| Crypto ereditate | Costo fiscale = valore alla data di ricezione | Calcolo manuale |
| Crypto ricevute in dono | Stesso del precedente | Calcolo manuale |
| Wallet personali esterni | Richiedono rigo RW separato | Aggiungere manualmente |
| E-money token | Rilevante ma non mappato nel CSV Coinbase | Verificare presenza e classificare |
