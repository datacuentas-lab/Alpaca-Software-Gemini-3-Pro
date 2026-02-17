import pandas as pd
import numpy as np
from config.settings import Config
import logging

logger = logging.getLogger("TradingBot")

class MovingAverageCrossover:
    def __init__(self, short_window=Config.SMA_SHORT, long_window=Config.SMA_LONG):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signal(self, data):
        """
        Generates a trading signal based on SMA Crossover.
        
        Args:
            data (pd.DataFrame): OHLCV data with 'Close' column.
            
        Returns:
            dict: Structured signal output.
        """
        if len(data) < self.long_window:
            logger.warning("Not enough data to calculate SMAs")
            return None

        df = data.copy()
        df['SMA_Short'] = df['Close'].rolling(window=self.short_window).mean()
        df['SMA_Long'] = df['Close'].rolling(window=self.long_window).mean()

        # Get the last two rows to check for crossover
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        signal = "HOLD"
        confidence = 0.0

        # Crossover Logic:
        # Buy: Short crosses above Long
        if prev_row['SMA_Short'] <= prev_row['SMA_Long'] and last_row['SMA_Short'] > last_row['SMA_Long']:
            signal = "BUY"
            confidence = 1.0
        # Sell: Short crosses below Long
        elif prev_row['SMA_Short'] >= prev_row['SMA_Long'] and last_row['SMA_Short'] < last_row['SMA_Long']:
            signal = "SELL"
            confidence = 1.0

        return {
            "symbol": Config.SYMBOL,
            "signal": signal,
            "confidence": confidence,
            "timestamp": last_row.name.isoformat() if hasattr(last_row.name, 'isoformat') else str(last_row.name)
        }
