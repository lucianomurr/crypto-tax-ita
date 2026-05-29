"""Test parsing e normalizzazione CSV Coinbase."""
import io
import pytest
import pandas as pd
from modules.csv_loader import load_coinbase_csv_from_buffer, TRANSACTION_TYPES


class TestLoadCoinbaseCsv:
    def test_loads_correct_row_count(self, coinbase_csv_buffer):
        from modules.csv_loader import load_coinbase_csv_from_buffer
        df = load_coinbase_csv_from_buffer(coinbase_csv_buffer)
        assert len(df) == 7

    def test_required_columns_present(self, loaded_df):
        required = {"timestamp", "date", "tx_type", "asset", "quantity",
                    "price_currency", "price_orig", "subtotal_orig", "total_orig"}
        assert required.issubset(set(loaded_df.columns))

    def test_sorted_by_timestamp_ascending(self, loaded_df):
        timestamps = loaded_df["timestamp"].tolist()
        assert timestamps == sorted(timestamps)

    def test_transaction_types_normalized(self, loaded_df):
        valid_types = set(TRANSACTION_TYPES.values()) | {"OTHER"}
        assert set(loaded_df["tx_type"].unique()).issubset(valid_types)

    def test_buy_mapped_correctly(self, loaded_df):
        buys = loaded_df[loaded_df["tx_type"] == "BUY"]
        assert len(buys) >= 2

    def test_sell_mapped_correctly(self, loaded_df):
        sells = loaded_df[loaded_df["tx_type"] == "SELL"]
        assert len(sells) >= 1

    def test_staking_mapped_correctly(self, loaded_df):
        staking = loaded_df[loaded_df["tx_type"] == "STAKING"]
        assert len(staking) >= 1

    def test_euro_symbol_stripped_from_prices(self, loaded_df):
        assert loaded_df["price_orig"].dtype in (float, "float64")
        assert loaded_df["total_orig"].dtype in (float, "float64")
        assert (loaded_df["price_orig"] >= 0).all()

    def test_quantity_always_positive(self, loaded_df):
        assert (loaded_df["quantity"] >= 0).all()

    def test_date_is_date_object(self, loaded_df):
        import datetime
        assert isinstance(loaded_df["date"].iloc[0], datetime.date)

    def test_price_currency_uppercase(self, loaded_df):
        assert loaded_df["price_currency"].str.isupper().all()


class TestTransactionTypeMapping:
    def test_buy_variants(self):
        assert TRANSACTION_TYPES["buy"] == "BUY"
        assert TRANSACTION_TYPES["advanced trade buy"] == "BUY"

    def test_sell_variants(self):
        assert TRANSACTION_TYPES["sell"] == "SELL"

    def test_staking_variants(self):
        assert TRANSACTION_TYPES["staking income"] == "STAKING"
        assert TRANSACTION_TYPES["rewards income"] == "STAKING"
        assert TRANSACTION_TYPES["inflation reward"] == "STAKING"

    def test_neutral_variants(self):
        assert TRANSACTION_TYPES["retail staking transfer"] == "NEUTRAL"
        assert TRANSACTION_TYPES["retail unstaking transfer"] == "NEUTRAL"
        assert TRANSACTION_TYPES["asset migration"] == "NEUTRAL"

    def test_earn_variants(self):
        assert TRANSACTION_TYPES["learning reward"] == "EARN"
        assert TRANSACTION_TYPES["coinbase earn"] == "EARN"


class TestMalformedCsv:
    def test_bad_lines_skipped(self):
        csv = (
            "Transactions\n"
            "User,Test,uuid\n"
            "ID,Timestamp,Transaction Type,Asset,Quantity Transacted,"
            "Price Currency,Price at Transaction,Subtotal,"
            "Total (inclusive of fees and/or spread),Fees and/or Spread,Notes,"
            "Sender Address,Recipient Address\n"
            "x1,2025-01-10 10:00:00 UTC,Buy,BTC,0.1,EUR,€40000,€4000,€4005,€5,,,\n"
            "RIGA_MALFORMATA\n"
            "x2,2025-06-01 10:00:00 UTC,Sell,BTC,0.1,EUR,€50000,€5000,€4995,€5,,,\n"
        )
        df = load_coinbase_csv_from_buffer(io.BytesIO(csv.encode()))
        assert len(df) >= 2
