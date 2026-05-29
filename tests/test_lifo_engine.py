"""Test motore LIFO — il cuore del calcolo fiscale."""
import pytest
from datetime import date
from modules.lifo_engine import LIFOEngine, Lot, Disposal


@pytest.fixture
def engine():
    return LIFOEngine()


class TestAddLot:
    def test_add_single_lot(self, engine):
        engine.add_lot("BTC", 1.0, 30000.0, date(2025, 1, 1))
        assert engine.get_balance("BTC") == pytest.approx(1.0)

    def test_add_multiple_lots_accumulate(self, engine):
        engine.add_lot("BTC", 0.3, 9000.0, date(2025, 1, 1))
        engine.add_lot("BTC", 0.2, 8000.0, date(2025, 3, 1))
        assert engine.get_balance("BTC") == pytest.approx(0.5)

    def test_zero_quantity_ignored(self, engine):
        engine.add_lot("BTC", 0.0, 0.0, date(2025, 1, 1))
        assert engine.get_balance("BTC") == pytest.approx(0.0)

    def test_multiple_assets_independent(self, engine):
        engine.add_lot("BTC", 1.0, 50000.0, date(2025, 1, 1))
        engine.add_lot("ETH", 2.0, 6000.0, date(2025, 1, 1))
        assert engine.get_balance("BTC") == pytest.approx(1.0)
        assert engine.get_balance("ETH") == pytest.approx(2.0)


class TestLIFOOrdering:
    def test_lifo_sells_last_lot_first(self, engine):
        """LIFO: il lotto acquistato per ultimo deve essere venduto per primo."""
        engine.add_lot("BTC", 0.3, 20000.0, date(2025, 1, 1))  # lotto 1
        engine.add_lot("BTC", 0.2, 25000.0, date(2025, 3, 1))  # lotto 2 (ultimo)

        d = engine.sell("BTC", 0.2, 30000.0, date(2025, 9, 1))

        # Con LIFO, deve usare il lotto 2 (costo 25000 per 0.2 BTC)
        assert d.cost_basis_eur == pytest.approx(25000.0)
        assert d.gain_loss_eur == pytest.approx(5000.0)

    def test_lifo_partial_lot(self, engine):
        """Vendita parziale del lotto più recente."""
        engine.add_lot("BTC", 0.3, 20000.0, date(2025, 1, 1))
        engine.add_lot("BTC", 0.4, 28000.0, date(2025, 6, 1))

        d = engine.sell("BTC", 0.2, 10000.0, date(2025, 9, 1))

        # 0.2 / 0.4 = 50% del lotto 2 → costo = 28000 * 0.5 = 14000
        assert d.cost_basis_eur == pytest.approx(14000.0)
        assert d.gain_loss_eur == pytest.approx(-4000.0)  # minusvalenza
        # Il lotto 2 deve avere ancora 0.2 BTC residui
        assert engine.get_balance("BTC") == pytest.approx(0.5)

    def test_lifo_consumes_multiple_lots(self, engine):
        """Vendita che consuma più lotti partendo dall'ultimo."""
        engine.add_lot("BTC", 0.1, 3000.0, date(2025, 1, 1))   # lotto 1: 0.1 BTC @ 30000
        engine.add_lot("BTC", 0.1, 4000.0, date(2025, 6, 1))   # lotto 2: 0.1 BTC @ 40000

        d = engine.sell("BTC", 0.15, 7500.0, date(2025, 9, 1))

        # Prima consuma tutto il lotto 2 (0.1 BTC @ 4000)
        # poi 0.05 BTC dal lotto 1 (0.05/0.1 * 3000 = 1500)
        expected_cost = 4000.0 + 1500.0
        assert d.cost_basis_eur == pytest.approx(expected_cost)
        assert engine.get_balance("BTC") == pytest.approx(0.05)


class TestGainLoss:
    def test_plusvalenza(self, engine):
        engine.add_lot("ETH", 1.0, 2000.0, date(2025, 1, 1))
        d = engine.sell("ETH", 1.0, 3000.0, date(2025, 6, 1))
        assert d.gain_loss_eur == pytest.approx(1000.0)
        assert d.proceeds_eur == pytest.approx(3000.0)
        assert d.cost_basis_eur == pytest.approx(2000.0)

    def test_minusvalenza(self, engine):
        engine.add_lot("ETH", 1.0, 2000.0, date(2025, 1, 1))
        d = engine.sell("ETH", 1.0, 1500.0, date(2025, 6, 1))
        assert d.gain_loss_eur == pytest.approx(-500.0)

    def test_pareggio(self, engine):
        engine.add_lot("ETH", 1.0, 2000.0, date(2025, 1, 1))
        d = engine.sell("ETH", 1.0, 2000.0, date(2025, 6, 1))
        assert d.gain_loss_eur == pytest.approx(0.0)


class TestErrors:
    def test_insufficient_balance_raises(self, engine):
        engine.add_lot("BTC", 0.1, 5000.0, date(2025, 1, 1))
        with pytest.raises(ValueError, match="Saldo insufficiente"):
            engine.sell("BTC", 0.5, 25000.0, date(2025, 6, 1))

    def test_sell_unknown_asset_raises(self, engine):
        with pytest.raises(ValueError, match="Saldo insufficiente"):
            engine.sell("DOGE", 100.0, 10.0, date(2025, 1, 1))


class TestBalances:
    def test_get_all_balances(self, engine):
        engine.add_lot("BTC", 0.5, 15000.0, date(2025, 1, 1))
        engine.add_lot("ETH", 2.0, 4000.0, date(2025, 1, 1))
        engine.sell("ETH", 1.0, 2500.0, date(2025, 6, 1))

        balances = engine.get_all_balances()
        assert balances["BTC"] == pytest.approx(0.5)
        assert balances["ETH"] == pytest.approx(1.0)

    def test_zero_balance_excluded(self, engine):
        engine.add_lot("BTC", 1.0, 50000.0, date(2025, 1, 1))
        engine.sell("BTC", 1.0, 55000.0, date(2025, 6, 1))

        balances = engine.get_all_balances()
        assert "BTC" not in balances

    def test_disposals_recorded(self, engine):
        engine.add_lot("BTC", 1.0, 50000.0, date(2025, 1, 1))
        engine.sell("BTC", 0.5, 30000.0, date(2025, 6, 1))
        engine.sell("BTC", 0.5, 28000.0, date(2025, 9, 1))

        assert len(engine.disposals) == 2
