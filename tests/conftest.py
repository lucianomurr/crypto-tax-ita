"""Fixtures condivise tra tutti i test."""
import io
import sys
import os
from datetime import date

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── CSV Coinbase formato EU (3 righe header + dati) ────────────────────────
COINBASE_EU_CSV = """\
Transactions
User,Test User,00000000-0000-0000-0000-000000000000
ID,Timestamp,Transaction Type,Asset,Quantity Transacted,Price Currency,Price at Transaction,Subtotal,Total (inclusive of fees and/or spread),Fees and/or Spread,Notes,Sender Address,Recipient Address
aaa001,2024-01-15 10:00:00 UTC,Buy,BTC,0.1,EUR,€35000,€3500,€3510,€10,,,
aaa002,2024-06-01 12:00:00 UTC,Buy,BTC,0.05,EUR,€40000,€2000,€2005,€5,,,
aaa003,2024-09-01 09:00:00 UTC,Sell,BTC,0.05,EUR,€45000,€2250,€2245,€5,,,
aaa004,2024-12-31 15:00:00 UTC,Staking Income,ETH,0.01,EUR,€2500,€25,€25,€0,,,
aaa005,2025-03-01 08:00:00 UTC,Buy,ETH,0.5,EUR,€2800,€1400,€1405,€5,,,
aaa006,2025-07-01 10:00:00 UTC,Sell,ETH,0.3,EUR,€3000,€900,€895,€5,,,
aaa007,2025-10-01 11:00:00 UTC,Convert,BTC,0.02,EUR,€50000,€1000,€995,€5,,,
"""


@pytest.fixture
def coinbase_csv_buffer():
    return io.BytesIO(COINBASE_EU_CSV.encode("utf-8"))


@pytest.fixture
def loaded_df(coinbase_csv_buffer):
    from modules.csv_loader import load_coinbase_csv_from_buffer
    return load_coinbase_csv_from_buffer(coinbase_csv_buffer)


@pytest.fixture
def empty_rates():
    """Tassi vuoti — usato quando il CSV è già in EUR."""
    return {}
