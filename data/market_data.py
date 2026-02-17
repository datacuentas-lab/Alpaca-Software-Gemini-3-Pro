import pandas as pd
import yfinance as yf
from broker.alpaca_adapter import AlpacaAdapter
from config.settings import Config
import logging

logger = logging.getLogger("TradingBot")

class MarketData:
    def __init__(self, use_alpaca=True):
        self.alpaca = AlpacaAdapter() if use_alpaca else None
        self.use_alpaca = use_alpaca

    def get_market_data(self, symbol, timeframe='1d', limit=100):
        """
        Fetches historical market data and returns a clean DataFrame with OHLCV structure.
        Ensures columns are: Open, High, Low, Close, Volume.
        """
        try:
            if self.use_alpaca and self.alpaca:
                df = self.alpaca.get_historical_data(symbol, timeframe, limit)
                if not df.empty:
                    # Alpaca returns columns like 'open', 'high', 'low', 'close', 'volume', 'trade_count', 'vwap'
                    # Standardize to Capitalized
                    df = df.rename(columns={
                        'open': 'Open',
                        'high': 'High', 
                        'low': 'Low', 
                        'close': 'Close', 
                        'volume': 'Volume'
                    })
                    return df[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            # Fallback to yfinance
            logger.info(f"Using yfinance fallback for {symbol}")
            ticker = yf.Ticker(symbol)
            # map timeframe for yf
            yf_tf = '1d' if timeframe == '1Day' else timeframe
            df = ticker.history(period='1mo', interval=yf_tf) # limit 100 approx 1mo
            
            if df.empty:
                logger.error(f"No data found for {symbol} via yfinance either.")
                return pd.DataFrame()
            
            return df[['Open', 'High', 'Low', 'Close', 'Volume']]

        except Exception as e:
            logger.error(f"Error in data layer: {e}")
            return pd.DataFrame()

