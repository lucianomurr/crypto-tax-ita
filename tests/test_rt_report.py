"""Test calcolo Quadro RT — plusvalenze, minusvalenze, franchigia."""
import pytest
from modules.rt_report import compute_rt_data


class TestComputeRtData:
    def test_returns_dict_with_expected_keys(self, loaded_df, empty_rates):
        rt = compute_rt_data(loaded_df, empty_rates, tax_year=2025)
        assert "disposals" in rt
        assert "summary" in rt
        assert "errors" in rt
        assert "balances" in rt

    def test_disposals_only_in_tax_year(self, loaded_df, empty_rates):
        rt = compute_rt_data(loaded_df, empty_rates, tax_year=2025)
        if not rt["disposals"].empty:
            years = rt["disposals"]["Data"].apply(lambda d: d.year).unique()
            assert all(y == 2025 for y in years)

    def test_summary_fields_when_disposals_exist(self, loaded_df, empty_rates):
        rt = compute_rt_data(loaded_df, empty_rates, tax_year=2025)
        if not rt["disposals"].empty:
            s = rt["summary"]
            assert "Totale_Plusvalenze_EUR" in s
            assert "Totale_Minusvalenze_EUR" in s
            assert "Reddito_Netto_EUR" in s
            assert "Imposta_Dovuta_EUR" in s

    def test_no_disposals_returns_empty(self, loaded_df, empty_rates):
        """Anno senza vendite → disposals vuoto, summary vuoto."""
        rt = compute_rt_data(loaded_df, empty_rates, tax_year=2022)
        assert rt["disposals"].empty
        assert rt["summary"] == {}

    def test_imposta_non_negative(self, loaded_df, empty_rates):
        rt = compute_rt_data(loaded_df, empty_rates, tax_year=2025)
        if rt["summary"]:
            assert rt["summary"]["Imposta_Dovuta_EUR"] >= 0

    def test_reddito_netto_is_plus_minus_minus(self, loaded_df, empty_rates):
        rt = compute_rt_data(loaded_df, empty_rates, tax_year=2025)
        if rt["summary"]:
            s = rt["summary"]
            expected = s["Totale_Plusvalenze_EUR"] - s["Totale_Minusvalenze_EUR"]
            assert s["Reddito_Netto_EUR"] == pytest.approx(expected, abs=0.01)

    def test_balances_non_negative(self, loaded_df, empty_rates):
        rt = compute_rt_data(loaded_df, empty_rates, tax_year=2025)
        for asset, qty in rt["balances"].items():
            assert qty >= 0, f"Saldo negativo per {asset}: {qty}"


class TestFranchigia:
    def test_2024_franchigia_applied_when_below(self, loaded_df, empty_rates):
        """Anno 2024: se reddito netto < 2000€ → imposta = 0."""
        rt = compute_rt_data(loaded_df, empty_rates, tax_year=2024)
        if rt["summary"]:
            s = rt["summary"]
            if s["Reddito_Netto_EUR"] < 2000:
                assert s["Imposta_Dovuta_EUR"] == 0.0

    def test_2025_no_franchigia(self, loaded_df, empty_rates):
        """Anno 2025: nessuna franchigia → se reddito > 0, imposta > 0."""
        rt = compute_rt_data(loaded_df, empty_rates, tax_year=2025)
        if rt["summary"] and rt["summary"]["Reddito_Netto_EUR"] > 0:
            assert rt["summary"]["Imposta_Dovuta_EUR"] > 0

    def test_tax_rate_26_percent_2025(self, loaded_df, empty_rates):
        """Anno 2025: aliquota 26%."""
        rt = compute_rt_data(loaded_df, empty_rates, tax_year=2025)
        if rt["summary"] and rt["summary"]["Reddito_Netto_EUR"] > 0:
            s = rt["summary"]
            expected_tax = s["Reddito_Netto_EUR"] * 0.26
            assert s["Imposta_Dovuta_EUR"] == pytest.approx(expected_tax, abs=0.01)


class TestLIFOIntegration:
    """Test end-to-end che il calcolo LIFO sia coerente con il motore."""

    def test_plusvalenza_with_known_data(self, empty_rates):
        """Verifica calcolo LIFO con dati noti."""
        import io
        csv = (
            "Transactions\n"
            "User,Test,uuid\n"
            "ID,Timestamp,Transaction Type,Asset,Quantity Transacted,"
            "Price Currency,Price at Transaction,Subtotal,"
            "Total (inclusive of fees and/or spread),Fees and/or Spread,Notes,"
            "Sender Address,Recipient Address\n"
            # Acquisto 1: 0.3 BTC @ 20000 EUR totale
            "x1,2025-01-01 10:00:00 UTC,Buy,BTC,0.3,EUR,€66666,€20000,€20000,€0,,,\n"
            # Acquisto 2: 0.2 BTC @ 25000 EUR totale (ULTIMO → usato per primo con LIFO)
            "x2,2025-03-01 10:00:00 UTC,Buy,BTC,0.2,EUR,€125000,€25000,€25000,€0,,,\n"
            # Vendita: 0.2 BTC a 30000 EUR → usa lotto 2 (LIFO) → plusvalenza 5000
            "x3,2025-09-01 10:00:00 UTC,Sell,BTC,0.2,EUR,€150000,€30000,€30000,€0,,,\n"
        )
        from modules.csv_loader import load_coinbase_csv_from_buffer
        df = load_coinbase_csv_from_buffer(io.BytesIO(csv.encode()))
        rt = compute_rt_data(df, empty_rates, tax_year=2025)

        assert not rt["disposals"].empty
        s = rt["summary"]
        assert s["Totale_Plusvalenze_EUR"] == pytest.approx(5000.0, abs=1.0)
        assert s["Totale_Minusvalenze_EUR"] == pytest.approx(0.0, abs=0.01)
        assert s["Reddito_Netto_EUR"] == pytest.approx(5000.0, abs=1.0)
        assert s["Imposta_Dovuta_EUR"] == pytest.approx(1300.0, abs=1.0)

    def test_historical_lots_used_in_current_year(self, empty_rates):
        """Acquisto in anno precedente, vendita nell'anno corrente."""
        import io
        csv = (
            "Transactions\n"
            "User,Test,uuid\n"
            "ID,Timestamp,Transaction Type,Asset,Quantity Transacted,"
            "Price Currency,Price at Transaction,Subtotal,"
            "Total (inclusive of fees and/or spread),Fees and/or Spread,Notes,"
            "Sender Address,Recipient Address\n"
            "x1,2024-06-01 10:00:00 UTC,Buy,ETH,1.0,EUR,€2000,€2000,€2000,€0,,,\n"
            "x2,2025-03-01 10:00:00 UTC,Sell,ETH,1.0,EUR,€3000,€3000,€3000,€0,,,\n"
        )
        from modules.csv_loader import load_coinbase_csv_from_buffer
        df = load_coinbase_csv_from_buffer(io.BytesIO(csv.encode()))
        rt = compute_rt_data(df, empty_rates, tax_year=2025)

        assert not rt["disposals"].empty
        assert rt["summary"]["Totale_Plusvalenze_EUR"] == pytest.approx(1000.0, abs=1.0)
