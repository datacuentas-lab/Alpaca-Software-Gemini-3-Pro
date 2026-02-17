import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Alpaca API Credentials
    API_KEY = os.getenv("ALPACA_API_KEY", "PK******************")
    API_SECRET = os.getenv("ALPACA_SECRET_KEY", "********************************")
    BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

    # Trading Parameters
    SYMBOL = "SPY"
    TIMEFRAME = "1Day"  # Daily candles
    SMA_SHORT = 20
    SMA_LONG = 50
    
    # Risk Management
    MAX_CAPITAL_PER_TRADE_PCT = 0.05  # 5%
    MAX_TRADES_PER_DAY = 2
    DAILY_STOP_LOSS_PCT = 0.03        # 3%
    STOP_LOSS_PCT = 0.02             # 2% per trade

    # Paths
    LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "trading.log")

    # Retry/Connection
    MAX_RETRIES = 3
    RETRY_DELAY = 5
