"""Test conversione valuta e logica tassi BCE."""
import pytest
import pandas as pd
from datetime import date
from unittest.mock import patch, MagicMock
from modules.exchange_rates import usd_to_eur, convert_to_eur


@pytest.fixture
def mock_rates():
    """Tassi fittizi: 1 USD = 0.92 EUR."""
    return {
        pd.Timestamp("2025-01-15"): 0.92,
        pd.Timestamp("2025-06-01"): 0.90,
        pd.Timestamp("2025-12-31"): 0.91,
    }


class TestUsdToEur:
    def test_converts_with_exact_date(self, mock_rates):
        result = usd_to_eur(100.0, date(2025, 1, 15), mock_rates)
        assert result == pytest.approx(92.0)

    def test_zero_amount_returns_zero(self, mock_rates):
        assert usd_to_eur(0.0, date(2025, 1, 15), mock_rates) == 0.0

    def test_falls_back_to_previous_day(self, mock_rates):
        """Se non esiste il tasso per la data, usa il giorno precedente."""
        # 2025-01-16 non è nei tassi, deve trovare 2025-01-15
        result = usd_to_eur(100.0, date(2025, 1, 16), mock_rates)
        assert result == pytest.approx(92.0)

    def test_raises_when_no_rate_found(self):
        empty_rates = {}
        with pytest.raises(ValueError, match="Nessun tasso BCE"):
            usd_to_eur(100.0, date(2025, 1, 15), empty_rates)

    def test_different_dates_use_correct_rate(self, mock_rates):
        r1 = usd_to_eur(100.0, date(2025, 1, 15), mock_rates)
        r2 = usd_to_eur(100.0, date(2025, 6, 1), mock_rates)
        assert r1 == pytest.approx(92.0)
        assert r2 == pytest.approx(90.0)


class TestConvertToEur:
    def test_eur_currency_returns_directly(self, mock_rates):
        """Se la valuta è già EUR, nessuna conversione."""
        result = convert_to_eur(100.0, "EUR", date(2025, 1, 15), mock_rates)
        assert result == pytest.approx(100.0)

    def test_usd_currency_converts(self, mock_rates):
        result = convert_to_eur(100.0, "USD", date(2025, 1, 15), mock_rates)
        assert result == pytest.approx(92.0)

    def test_unsupported_currency_raises(self, mock_rates):
        with pytest.raises(ValueError, match="Valuta non supportata"):
            convert_to_eur(100.0, "GBP", date(2025, 1, 15), mock_rates)

    def test_zero_eur_returns_zero(self, mock_rates):
        assert convert_to_eur(0.0, "EUR", date(2025, 1, 15), mock_rates) == 0.0

    def test_zero_usd_returns_zero(self, mock_rates):
        assert convert_to_eur(0.0, "USD", date(2025, 1, 15), mock_rates) == 0.0
