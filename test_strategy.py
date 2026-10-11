import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
from ArabicLearningStrategy import ArabicLearningStrategy


class StrategyTests(unittest.TestCase):
    def setUp(self):
        self.strategy = ArabicLearningStrategy({"dry_run": True, "runmode": SimpleNamespace(value="backtest")})
        self.strategy.dp = None

    def frame(self, prices):
        return pd.DataFrame({"close": prices, "volume": [10]*len(prices),
            "date": pd.date_range("2026-01-01", periods=len(prices), freq="h", tz="UTC")})

    def analyze(self, frame):
        result = self.strategy.populate_indicators(frame.copy(), {})
        result = self.strategy.populate_entry_trend(result, {})
        return self.strategy.populate_exit_trend(result, {})

    def test_flat_wait(self):
        df = self.analyze(self.frame([100]*70))
        self.assertEqual(df.iloc[-1]["rsi_simple"], 50)
        self.assertEqual(df.iloc[-1]["enter_long"], 0)
        self.assertEqual(df.iloc[-1]["exit_long"], 0)

    def test_downtrend_exit_no_entry(self):
        df = self.analyze(self.frame(list(range(100,30,-1))))
        self.assertEqual(df.iloc[-1]["exit_long"], 1)
        self.assertEqual(df.iloc[-1]["enter_long"], 0)

    def test_entry_and_zero_volume(self):
        frame = pd.DataFrame({"sma20": [110,110], "sma50": [100,100], "rsi_simple": [60,60], "volume": [10,0]})
        df = self.strategy.populate_entry_trend(frame,{})
        self.assertEqual(df["enter_long"].tolist(), [1,0])

    def test_no_lookahead_in_indicators(self):
        first = self.frame([100+i*.1+(i%3) for i in range(70)])
        prefix = self.analyze(first)
        extended = self.analyze(self.frame(first.close.tolist()+[10000]*5))
        pd.testing.assert_frame_equal(prefix,extended.iloc[:70].reset_index(drop=True))

    def test_live_mode_rejected(self):
        self.strategy.config["runmode"] = SimpleNamespace(value="live")
        with self.assertRaises(RuntimeError):
            self.strategy.bot_start()

    def test_stale_and_unclosed_entries_rejected(self):
        now = datetime.now(timezone.utc)
        self.strategy.dp = Mock()
        for age,allowed in [(100,False),(3601,True),(10000,False)]:
            df = pd.DataFrame({"date": [pd.Timestamp(now-timedelta(seconds=age))]})
            self.strategy.dp.get_analyzed_dataframe.return_value = (df,None)
            self.assertEqual(self.strategy.confirm_trade_entry("BTC/USD","market",1,100,"GTC",now,None,"long"),allowed)

if __name__ == "__main__":
    unittest.main()
