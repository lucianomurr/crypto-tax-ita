TAX_YEAR = 2025  # default per CLI
COST_METHOD = "LIFO"

COINBASE_CSV = "data/coinbase_export.csv"
EXCHANGE_RATES_CACHE = "data/exchange_rates.csv"
OUTPUT_RW = "output/report_RW_{year}.csv"
OUTPUT_RT = "output/report_RT_{year}.csv"

# Parametri fiscali per anno d'imposta
# Fonti: L.197/2022 (2023+), L.207/2024 (2025), L.208/2025 (2026+)
_PARAMS = {
    # anno: (tax_rate, exemption, ivaca_rate, ivaca_min)
    # exemption: soglia sotto cui l'imposta non è dovuta (franchigia)
    # ivaca: introdotta dal 2023 con L.197/2022
    2020: (0.26, 51645.69, 0.0,   0.0),
    2021: (0.26, 51645.69, 0.0,   0.0),
    2022: (0.26, 51645.69, 0.0,   0.0),
    2023: (0.26, 2000.0,   0.002, 12.0),
    2024: (0.26, 2000.0,   0.002, 12.0),
    2025: (0.26, 0.0,      0.002, 12.0),
    2026: (0.33, 0.0,      0.002, 12.0),
}
# Valori di default (aliquota 26%, nessuna franchigia, IVACA)
_DEFAULT_PARAMS = (0.26, 0.0, 0.002, 12.0)


def get_tax_params(year: int) -> dict:
    """Restituisce i parametri fiscali per l'anno d'imposta specificato."""
    rate, exemption, ivaca_rate, ivaca_min = _PARAMS.get(year, _DEFAULT_PARAMS)
    return {
        "tax_rate":   rate,
        "exemption":  exemption,   # franchigia: se gain netto < exemption → imposta = 0
        "ivaca_rate": ivaca_rate,
        "ivaca_min":  ivaca_min,
        "ivaca_applies": ivaca_rate > 0,
    }


# Alias compatibilità (usati nel CLI)
TAX_RATE   = get_tax_params(TAX_YEAR)["tax_rate"]
IVACA_RATE = get_tax_params(TAX_YEAR)["ivaca_rate"]
IVACA_MIN  = get_tax_params(TAX_YEAR)["ivaca_min"]
