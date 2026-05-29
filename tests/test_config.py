"""Test parametri fiscali per anno."""
import pytest
from config import get_tax_params


class TestGetTaxParams:
    def test_2025_no_exemption(self):
        p = get_tax_params(2025)
        assert p["exemption"] == 0.0
        assert p["tax_rate"] == 0.26
        assert p["ivaca_applies"] is True

    def test_2024_exemption_2000(self):
        p = get_tax_params(2024)
        assert p["exemption"] == 2000.0
        assert p["tax_rate"] == 0.26
        assert p["ivaca_applies"] is True

    def test_2023_exemption_2000(self):
        p = get_tax_params(2023)
        assert p["exemption"] == 2000.0
        assert p["ivaca_applies"] is True

    def test_2022_no_ivaca(self):
        p = get_tax_params(2022)
        assert p["ivaca_applies"] is False
        assert p["ivaca_rate"] == 0.0

    def test_2026_rate_33(self):
        p = get_tax_params(2026)
        assert p["tax_rate"] == 0.33
        assert p["exemption"] == 0.0

    def test_unknown_year_returns_default(self):
        p = get_tax_params(2030)
        assert "tax_rate" in p
        assert "exemption" in p
        assert "ivaca_rate" in p

    def test_ivaca_min_is_12(self):
        for year in (2023, 2024, 2025, 2026):
            assert get_tax_params(year)["ivaca_min"] == 12.0
