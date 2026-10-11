"""Educational strategy extension for the original Freqtrade engine.

Not a standalone trading engine, and not a profitability claim.
"""
from datetime import datetime, timezone
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class ArabicLearningStrategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False
    startup_candle_count = 60
    process_only_new_candles = True
    minimal_roi = {"0": 0.06}
    stoploss = -0.03
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False
    position_adjustment_enable = False
    order_types = {
        "entry": "market", "exit": "market", "stoploss": "market",
        "stoploss_on_exchange": False,
    }
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    def bot_start(self, **kwargs):
        if self.config.get("runmode").value == "live":
            raise RuntimeError("هذه الاستراتيجية معدة للتداول الوهمي فقط.")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma20"] = dataframe["close"].rolling(20).mean()
        dataframe["sma50"] = dataframe["close"].rolling(50).mean()
        change = dataframe["close"].diff()
        gains = change.clip(lower=0).rolling(14).mean()
        losses = (-change.clip(upper=0)).rolling(14).mean()
        dataframe["rsi_simple"] = 100 - 100 / (1 + gains / losses)
        dataframe.loc[(gains == 0) & (losses == 0), "rsi_simple"] = 50
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        entry = (
            (dataframe["sma20"] > dataframe["sma50"])
            & dataframe["rsi_simple"].between(45, 70)
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[entry, ["enter_long", "enter_tag"]] = (1, "trend_up_moderate_rsi")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        exit_condition = (
            ((dataframe["sma20"] < dataframe["sma50"]) | (dataframe["rsi_simple"] < 40))
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[exit_condition, ["exit_long", "exit_tag"]] = (1, "weak_trend_or_momentum")
        if self.dp and self.config.get("runmode").value == "dry_run" and not dataframe.empty:
            candle = dataframe.iloc[-1]
            age = (datetime.now(timezone.utc) - candle["date"].to_pydatetime()).total_seconds()
            if 3600 <= age <= 7500 and candle[["sma20", "sma50", "rsi_simple"]].notna().all():
                buy = candle["sma20"] > candle["sma50"] and 45 <= candle["rsi_simple"] <= 70 and candle["volume"] > 0
                sell = bool(candle["exit_long"])
                decision = "شراء محتمل" if buy else "خروج محتمل" if sell else "انتظار"
                reason = "اتجاه صاعد وزخم ضمن نطاق الدخول" if buy else "اتجاه ضعيف أو زخم منخفض" if sell else "شروط الدخول والخروج غير مكتملة"
                self.dp.send_msg(
                    f"Freqtrade الأصلي — محاكاة فقط\n{metadata['pair']}: {decision}\n"
                    f"بداية الشمعة UTC: {candle['date']}\n"
                    f"متوسط 20 ساعة: {candle['sma20']:.2f}؛ متوسط 50: {candle['sma50']:.2f}\n"
                    f"RSI البسيط: {candle['rsi_simple']:.1f}\nالسبب: {reason}.\n"
                    "الإشارة لا تعني تنفيذ صفقة؛ تأكيد التنفيذ يصل منفصلًا.\n"
                    "للأداء /profit وللصفقات /status — لا ضمان للربح."
                )
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force,
                            current_time, entry_tag, side, **kwargs) -> bool:
        if self.config.get("dry_run") is not True:
            return False
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe.empty:
            return False
        age = (current_time - dataframe.iloc[-1]["date"].to_pydatetime()).total_seconds()
        return 3600 <= age <= 7500
