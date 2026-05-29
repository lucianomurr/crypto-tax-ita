import pandas as pd
from config import get_tax_params
from modules.lifo_engine import LIFOEngine
from modules.exchange_rates import convert_to_eur

BUY_TYPES = {"BUY", "RECEIVE", "STAKING", "EARN"}
TAXABLE_SELL_TYPES = {"SELL", "CONVERT"}


def compute_rt_data(df: pd.DataFrame, rates: dict, tax_year: int = None) -> dict:
    """
    Calcola plusvalenze/minusvalenze (Quadro RT) con metodo LIFO.

    Parametri:
        df        – DataFrame normalizzato da csv_loader
        rates     – tassi BCE (vuoto se CSV già in EUR)
        tax_year  – anno d'imposta (default: config.TAX_YEAR)

    Elabora tutta la storia per costruire il corretto inventario LIFO,
    ma considera solo le disposals di tax_year come fiscalmente rilevanti.
    """
    if tax_year is None:
        from config import TAX_YEAR
        tax_year = TAX_YEAR

    params = get_tax_params(tax_year)
    tax_rate = params["tax_rate"]
    exemption = params["exemption"]

    engine = LIFOEngine()
    errors = []
    disposals_year = []

    for _, row in df.iterrows():
        tx = row["tx_type"]
        asset = row["asset"]
        qty = float(row["quantity"])
        tx_date = row["date"]
        currency = row["price_currency"]

        if tx == "NEUTRAL" or asset == "EUR" or qty <= 0:
            continue

        if tx in BUY_TYPES:
            try:
                cost_eur = convert_to_eur(float(row["total_orig"]), currency, tx_date, rates)
                engine.add_lot(asset, qty, cost_eur, tx_date)
            except ValueError as e:
                errors.append(f"[{tx_date}] {asset} {tx}: {e}")

        elif tx in TAXABLE_SELL_TYPES:
            try:
                proceeds_eur = convert_to_eur(float(row["subtotal_orig"]), currency, tx_date, rates)
                disposal = engine.sell(asset, qty, proceeds_eur, tx_date)

                if tx_date.year == tax_year:
                    disposals_year.append(
                        {
                            "Data": tx_date,
                            "Asset": asset,
                            "Tipo_TX": tx,
                            "Quantita_Venduta": round(qty, 8),
                            "Ricavo_EUR": round(disposal.proceeds_eur, 2),
                            "Costo_LIFO_EUR": round(disposal.cost_basis_eur, 2),
                            "PlusMinus_EUR": round(disposal.gain_loss_eur, 2),
                            "Tipo": "Plusvalenza" if disposal.gain_loss_eur >= 0 else "Minusvalenza",
                        }
                    )
            except ValueError as e:
                errors.append(f"[{tx_date}] {asset} {tx}: {e}")

    if not disposals_year:
        return {
            "disposals": pd.DataFrame(),
            "summary": {},
            "errors": errors,
            "balances": engine.get_all_balances(),
            "params": params,
        }

    disp_df = pd.DataFrame(disposals_year)

    total_plus = disp_df[disp_df["PlusMinus_EUR"] > 0]["PlusMinus_EUR"].sum()
    total_minus = abs(disp_df[disp_df["PlusMinus_EUR"] < 0]["PlusMinus_EUR"].sum())
    net = total_plus - total_minus

    # Applica franchigia: se guadagno netto < exemption, imposta = 0
    if exemption > 0 and net < exemption:
        imposta = 0.0
        note_franchigia = f"Reddito netto (€ {net:,.2f}) sotto la franchigia di € {exemption:,.0f} → imposta non dovuta"
    else:
        imposta = max(0.0, net * tax_rate)
        note_franchigia = None

    summary = {
        "Totale_Plusvalenze_EUR": round(total_plus, 2),
        "Totale_Minusvalenze_EUR": round(total_minus, 2),
        "Reddito_Netto_EUR": round(net, 2),
        "Franchigia_EUR": exemption,
        "Imposta_Dovuta_EUR": round(imposta, 2),
        "Aliquota": f"{tax_rate * 100:.0f}%",
        "Num_Operazioni": len(disposals_year),
        "Note_Franchigia": note_franchigia,
    }

    return {
        "disposals": disp_df,
        "summary": summary,
        "errors": errors,
        "balances": engine.get_all_balances(),
        "params": params,
    }
