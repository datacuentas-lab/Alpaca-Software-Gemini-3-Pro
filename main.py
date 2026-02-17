import logging
import time
import schedule
import argparse
from colorama import init, Fore, Style
from config.settings import Config
from broker.alpaca_adapter import AlpacaAdapter
from data.market_data import MarketData
from strategy.moving_average import MovingAverageCrossover
from risk.risk_engine import RiskEngine
from execution.executor import Executor

# Initialize colorama
init(autoreset=True)

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TradingBot")

def run_trading_cycle():
    logger.info(f"{Fore.CYAN}Starting Trading Cycle for {Config.SYMBOL}...")
    
    # 1. Initialize Components
    broker = AlpacaAdapter()
    if not broker.api:
        logger.error(f"{Fore.RED}Broker connection failed. Aborting cycle.")
        return

    data_feed = MarketData(use_alpaca=True)
    strategy = MovingAverageCrossover(Config.SMA_SHORT, Config.SMA_LONG)
    risk_engine = RiskEngine(broker)
    executor = Executor(broker, risk_engine)

    # 2. Fetch Data
    logger.info(f"Fetching market data for {Config.SYMBOL}...")
    df = data_feed.get_market_data(Config.SYMBOL, timeframe=Config.TIMEFRAME)
    if df.empty:
        logger.error(f"{Fore.RED}No market data available.")
        return
    
    current_price = df['Close'].iloc[-1]
    logger.info(f"Current Price of {Config.SYMBOL}: ${current_price:.2f}")

    # 3. Generate Signal
    logger.info("Analyzing market data...")
    signal = strategy.generate_signal(df)
    
    if not signal:
        logger.warning("No signal generated (insufficient data?)")
        return

    logger.info(f"{Fore.YELLOW}Signal: {signal['signal']} (Confidence: {signal['confidence']})")

    # 4. Execute Signal
    if signal['signal'] != 'HOLD':
        executor.execute_signal(signal, current_price)
    else:
        logger.info("Holding position. No trade execution required.")

    logger.info(f"{Fore.GREEN}Trading Cycle Completed.\n")

def main():
    parser = argparse.ArgumentParser(description='Algorithmic Trading Bot MVP')
    parser.add_argument('--loop', action='store_true', help='Run in a continuous loop')
    args = parser.parse_args()

    print(f"{Fore.MAGENTA}==========================================")
    print(f"{Fore.MAGENTA}   INSTITUTIONAL TRADING BOT - CORE v1.0  ")
    print(f"{Fore.MAGENTA}==========================================\n")

    if args.loop:
        logger.info("Starting in continuous loop mode (Daily Check).")
        # Schedule the job every day at market open or specific time?
        # For MVP loop, we'll run immediately then wait.
        run_trading_cycle() # Run once on start
        
        # Schedule next run
        schedule.every().day.at("09:30").do(run_trading_cycle) 
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run_trading_cycle()

if __name__ == "__main__":
    main()
