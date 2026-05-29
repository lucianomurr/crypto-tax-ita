from collections import defaultdict
from dataclasses import dataclass, field
from typing import List


@dataclass
class Lot:
    date: object
    quantity: float
    cost_eur: float
    asset: str


@dataclass
class Disposal:
    date: object
    asset: str
    quantity_sold: float
    proceeds_eur: float
    cost_basis_eur: float
    gain_loss_eur: float
    lots_detail: list = field(default_factory=list)


class LIFOEngine:
    def __init__(self):
        self.lots: dict[str, List[Lot]] = defaultdict(list)
        self.disposals: List[Disposal] = []

    def add_lot(self, asset: str, quantity: float, cost_eur: float, tx_date: object):
        if quantity <= 0:
            return
        self.lots[asset].append(Lot(tx_date, quantity, cost_eur, asset))

    def sell(
        self,
        asset: str,
        quantity: float,
        proceeds_eur: float,
        tx_date: object,
    ) -> Disposal:
        """Vende quantity di asset con metodo LIFO. Genera un Disposal."""
        stack = self.lots[asset]
        remaining = quantity
        cost_basis = 0.0
        lots_detail = []

        # LIFO: scorriamo dall'ultimo lotto (indice -1)
        while remaining > 1e-10 and stack:
            lot = stack[-1]
            if lot.quantity <= remaining + 1e-10:
                used_qty = lot.quantity
                cost_basis += lot.cost_eur
                lots_detail.append({
                    "lot_date": lot.date,
                    "qty_used": round(used_qty, 8),
                    "cost_eur": round(lot.cost_eur, 4),
                })
                remaining -= lot.quantity
                stack.pop()
            else:
                fraction = remaining / lot.quantity
                used_cost = lot.cost_eur * fraction
                cost_basis += used_cost
                lots_detail.append({
                    "lot_date": lot.date,
                    "qty_used": round(remaining, 8),
                    "cost_eur": round(used_cost, 4),
                })
                lot.quantity -= remaining
                lot.cost_eur -= used_cost
                remaining = 0.0

        if remaining > 1e-6:
            raise ValueError(
                f"Saldo insufficiente per {asset}: mancano {remaining:.8f} unità. "
                "Assicurati di caricare la cronologia completa (inclusi gli anni precedenti)."
            )

        disposal = Disposal(
            date=tx_date,
            asset=asset,
            quantity_sold=quantity,
            proceeds_eur=proceeds_eur,
            cost_basis_eur=cost_basis,
            gain_loss_eur=proceeds_eur - cost_basis,
            lots_detail=lots_detail,
        )
        self.disposals.append(disposal)
        return disposal

    def get_balance(self, asset: str) -> float:
        return sum(lot.quantity for lot in self.lots[asset])

    def get_all_balances(self) -> dict:
        return {asset: self.get_balance(asset) for asset in self.lots if self.get_balance(asset) > 1e-10}
