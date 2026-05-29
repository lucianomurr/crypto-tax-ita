# Checklist Operativa

Lista di controllo da seguire ogni anno prima di presentare la dichiarazione.

---

## Prima di usare l'app

- [ ] Scaricare il CSV da Coinbase con **tutta la cronologia** (non solo l'anno corrente)
  - Coinbase → Menu → Strumenti → Rapporti → Cronologia transazioni → Tutta la cronologia
- [ ] Verificare che il CSV contenga transazioni fino al **31 dicembre** dell'anno d'imposta
- [ ] Verificare la connessione internet (necessaria per prezzi CoinGecko e tassi BCE se CSV in USD)
- [ ] Inserire la CoinGecko API key nel file `.env` (opzionale ma consigliato per velocità)

---

## Durante l'elaborazione

- [ ] Cliccare **"Scarica prezzi storici"** per ottenere i prezzi reali al 01/01 e 31/12
- [ ] Verificare che il badge nel tab Quadro RW mostri "prezzi reali CoinGecko" per tutti gli asset
- [ ] Controllare eventuali **avvisi di elaborazione** (transazioni con saldo insufficiente)
- [ ] Verificare che non ci siano transazioni classificate come **OTHER** con rilevanza fiscale

---

## Verifica dei risultati – Quadro RW

- [ ] Confrontare la **quantità al 31/12** calcolata dall'app con il saldo effettivo su Coinbase
- [ ] Verificare il **valore al 31/12** con il prezzo di mercato reale alla data
- [ ] Controllare che ogni asset con IVACA ≥ € 12 abbia il valore corretto nel campo "IVACA dovuta"
- [ ] Aggiungere righe separate per eventuali **wallet personali** (Ledger, MetaMask ecc.) non gestiti dall'app

---

## Verifica dei risultati – Quadro RT

- [ ] Confrontare i totali con il **Coinbase Tax Center** (nota: Coinbase usa FIFO, l'app usa LIFO → i valori differiscono)
- [ ] Verificare che tutte le **conversioni** siano state trattate come eventi tassabili
- [ ] Controllare le **minusvalenze degli anni precedenti** da portare in compensazione
- [ ] Verificare la corretta applicazione della **franchigia** (anni 2023–2024) o della sua abolizione (2025+)

---

## Prima di presentare la dichiarazione

- [ ] Consegnare i report al **commercialista** per la compilazione definitiva del modello
- [ ] Verificare con il commercialista il trattamento di eventuali operazioni speciali (airdrops, NFT, DeFi)
- [ ] Conservare tutti i CSV originali e i report generati per **almeno 5 anni**
- [ ] Preparare le **ricevute F24** per i versamenti IVACA e imposta plusvalenze

---

## Nota su Coinbase Tax Center

Coinbase mette a disposizione un [Tax Center dedicato](https://www.coinbase.com/tax-center) con un riepilogo delle plusvalenze/minusvalenze.

> ⚠️ I dati del Coinbase Tax Center usano il metodo **FIFO** (First In First Out), che è lo standard USA. In Italia si applica il metodo **LIFO**, quindi i valori **differiscono** e il Tax Center di Coinbase non è utilizzabile direttamente per la dichiarazione italiana.
