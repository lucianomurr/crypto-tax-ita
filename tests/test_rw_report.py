"""Test calcolo Quadro RW e IVACA."""
import pytest
from modules.rw_report import compute_rw_data


class TestComputeRwData:
    def test_returns_dataframe(self, loaded_df, empty_rates):
        rw = compute_rw_data(loaded_df, empty_rates, tax_year=2025)
        import pandas as pd
        assert isinstance(rw, pd.DataFrame)

    def test_expected_columns_present(self, loaded_df, empty_rates):
        rw = compute_rw_data(loaded_df, empty_rates, tax_year=2025)
        expected = {"Asset", "Valore_Iniziale_EUR", "Valore_Finale_EUR",
                    "IVACA_Calcolata_EUR", "IVACA_Dovuta_EUR", "Quantita_31dic"}
        assert expected.issubset(set(rw.columns))

    def test_eur_asset_excluded(self, loaded_df, empty_rates):
        rw = compute_rw_data(loaded_df, empty_rates, tax_year=2025)
        assert "EUR" not in rw["Asset"].values

    def test_ivaca_not_due_below_threshold(self, loaded_df, empty_rates):
        """IVACA non dovuta se < €12."""
        rw = compute_rw_data(loaded_df, empty_rates, tax_year=2025)
        # Tutti gli asset con IVACA calcolata < 12 devono avere IVACA dovuta = 0
        below = rw[rw["IVACA_Calcolata_EUR"] < 12]
        assert (below["IVACA_Dovuta_EUR"] == 0).all()

    def test_ivaca_due_above_threshold(self, loaded_df, empty_rates):
        """IVACA dovuta se ≥ €12."""
        rw = compute_rw_data(loaded_df, empty_rates, tax_year=2025)
        above = rw[rw["IVACA_Calcolata_EUR"] >= 12]
        if not above.empty:
            assert (above["IVACA_Dovuta_EUR"] > 0).all()

    def test_ivaca_zero_pre_2023(self, loaded_df, empty_rates):
        """IVACA non esisteva prima del 2023."""
        rw = compute_rw_data(loaded_df, empty_rates, tax_year=2022)
        if not rw.empty:
            assert (rw["IVACA_Calcolata_EUR"] == 0).all()
            assert (rw["IVACA_Dovuta_EUR"] == 0).all()

    def test_quantities_non_negative(self, loaded_df, empty_rates):
        rw = compute_rw_data(loaded_df, empty_rates, tax_year=2025)
        assert (rw["Quantita_31dic"] >= 0).all()
        assert (rw["Quantita_01gen"] >= 0).all()

    def test_values_non_negative(self, loaded_df, empty_rates):
        rw = compute_rw_data(loaded_df, empty_rates, tax_year=2025)
        assert (rw["Valore_Finale_EUR"] >= 0).all()
        assert (rw["Valore_Iniziale_EUR"] >= 0).all()

    def test_ivaca_formula(self, loaded_df, empty_rates):
        """IVACA calcolata = valore finale × 0.002."""
        rw = compute_rw_data(loaded_df, empty_rates, tax_year=2025)
        for _, row in rw.iterrows():
            expected = round(row["Valore_Finale_EUR"] * 0.002, 2)
            assert row["IVACA_Calcolata_EUR"] == pytest.approx(expected, abs=0.01)
