import logging
from config.settings import Config
from broker.alpaca_adapter import AlpacaAdapter
from risk.risk_engine import RiskEngine
import math

logger = logging.getLogger("TradingBot")

class Executor:
    def __init__(self, broker: AlpacaAdapter, risk_engine: RiskEngine):
        self.broker = broker
        self.risk_engine = risk_engine

    def execute_signal(self, signal, current_price):
        """
        Executes a trade based on the generated signal.
        
        Args:
            signal (dict): The signal from Strategy Engine.
            current_price (float): The latest price of the asset.
        """
        symbol = signal['symbol']
        direction = signal['signal']
        
        if direction == 'HOLD':
            logger.info("Signal is HOLD. No action taken.")
            return

        # 1. Validate with Risk Engine
        allowed, risk_msg = self.risk_engine.check_trade(signal)
        if not allowed:
            logger.warning(f"Trade blocked by Risk Engine: {risk_msg}")
            return

        # 2. Calculate Position Size
        # risk_msg is the max_position_value if allowed is True (from previous tool implementation logic)
        # Wait, I returned `True, max_position_value` in risk_engine.check_trade?
        # Let's double check risk_engine logic.
        # Yes: `return True, max_position_value`.
        
        max_usd_position = risk_msg
        
        # Calculate quantity (shares/contracts)
        # Round down to integer or allowable lot size. Alpaca allows fractional in paper, but integer is safer.
        qty = math.floor(max_usd_position / current_price)
        
        if qty <= 0:
            logger.warning(f"Calculated quantity is 0 (Capital: {max_usd_position}, Price: {current_price})")
            return

        # 3. Submit Order
        try:
            side = 'buy' if direction == 'BUY' else 'sell'
            # Check existing position first?
            # If we are reversing, we mighty need to close existing.
            # But prompt says "MVP", so maybe just open new position.
            # Actually, SMA crossover usually implies "Long Only" or "Long/Short". 
            # If we hold Long and get Sell signal, we should Close Long.
            # Let's assume Long Only for MVP simplicity unless "Short" is specified.
            # Usually: Buy = Enter Long, Sell = Exit Long (or Enter Short).
            # The strategy returns BUY/SELL.
            # Let's implement: 
            #   BUY -> If no position, open Long. If Short, Close Short & Open Long (flip).
            #   SELL -> If Long, Close Long. If no position, Open Short? or Stay Flat?
            # Given "MVP", let's do:
            #   BUY -> Open Long (if not already long)
            #   SELL -> Close Long (if long)
            
            # Check current position
            positions = self.broker.get_positions()
            current_qty = 0
            for p in positions:
                if p.symbol == symbol:
                    current_qty = float(p.qty)
                    break
            
            if direction == 'BUY':
                if current_qty > 0:
                    logger.info("Already Long. Holding.")
                    return
                elif current_qty < 0:
                     # Close Short first (not implemented for MVP, assuming long-only start)
                     self.broker.submit_order(symbol, abs(current_qty), 'buy') # close short
                
                # Open Long
                order = self.broker.submit_order(symbol, qty, 'buy')
                if order:
                    logger.info(f"Executed BUY {qty} shares of {symbol} at ~{current_price}")
                    self.risk_engine.record_trade() # update daily stats
            
            elif direction == 'SELL':
                if current_qty > 0:
                    # Close Long
                    order = self.broker.submit_order(symbol, abs(current_qty), 'sell')
                    if order:
                        logger.info(f"Executed SELL {abs(current_qty)} shares of {symbol} to close position.")
                        self.risk_engine.record_trade()
                else:
                    logger.info("No position to Sell.")

        except Exception as e:
            logger.error(f"Execution failed: {e}")

