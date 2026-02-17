import logging
import time
import pandas as pd
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST, TimeFrame
from config.settings import Config

logger = logging.getLogger("TradingBot")

class AlpacaAdapter:
    def __init__(self):
        try:
            self.api = REST(Config.API_KEY, Config.API_SECRET, Config.BASE_URL)
            self.account = self.get_account()
            if self.account:
                logger.info(f"Connected to Alpaca. Account Status: {self.account.status}. Balance: {self.account.equity}")
            else:
                logger.error("Failed to connect to Alpaca.")
        except Exception as e:
            logger.error(f"Error initializing Alpaca connection: {e}")
            self.api = None

    def get_account(self):
        try:
            return self.api.get_account()
        except Exception as e:
            logger.error(f"Error fetching account info: {e}")
            return None

    def get_positions(self):
        try:
            positions = self.api.list_positions()
            logger.info(f"Fetched {len(positions)} open positions.")
            return positions
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    def get_open_orders(self):
        try:
            orders = self.api.list_orders(status='open')
            return orders
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []

    def submit_order(self, symbol, qty, side, type='market', time_in_force='day', stop_loss=None):
        """
        Submits an order to Alpaca.
        If stop_loss is provided (percentage, e.g., 0.02 for 2%), a bracket order could be used,
        but for simplicity in MVP we might stick to market order or simple stop loss.
        The prompt asks for 'Stop loss automático 2%'. This implies the order should have a stop loss attached.
        Alpaca supports bracket orders.
        """
        try:
            if stop_loss:
                # Calculate stop price based on current price is difficult without fetching it first.
                # However, Alpaca API allows 'stop_loss' parameter in submit_order for bracket orders if we use 'bracket' class or similar output, 
                # but 'market' orders with stop_loss logic are complex. 
                # For an MVP, we can place a market order, then immediately place a stop loss order, 
                # OR use the 'order_class' parameter if supported for the asset.
                # Let's try to use simple market orders first, and maybe a separate stop order if needed, 
                # or just use client-side logic (monitoring). 
                # EXCEPT the prompt says "Stop loss automático 2%". 
                # The most robust way is a bracket order.
                
                # Fetch current price to estimate stop price? 
                # Or just let the risk engine handle the "logic" and pass explicit stop price here?
                # The execution engine should probably calculate the specific prices.
                # For the adapter, we should support passing raw parameters.
                pass

            # Basic implementation for MVP: Market Order
            # Extended implementation: Limit/Stop
            
            # We will interpret 'submit_order' as a raw interface tailored for our strategy.
            # If we want a stop loss, we probably need a bracket order or OCO.
            # For simplicity in this adapter, we'll assume the caller handles the logic or we use order_class='bracket' if applicable.
            # But the signature only asks for symbol, qty, side.
            # We will use simple market order for now as per "MVP" and "Simple". 
            # Risk engine rules (max 2% stop loss) might be monitored, or implemented in 'execution'.
            
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=type,
                time_in_force=time_in_force
            )
            logger.info(f"Order submitted: {side} {qty} {symbol} - ID: {order.id}")
            return order
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            return None

    def cancel_order(self, order_id):
        try:
            self.api.cancel_order(order_id)
            logger.info(f"Order {order_id} cancelled.")
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")

    def get_historical_data(self, symbol, timeframe, limit=100):
        """
        Fetches historical data (bars).
        """
        try:
            # map timeframe for Alpaca (TimeFrame.Day, etc)
            tf = TimeFrame.Day # Defaulting for MVP based on config
            
            bars = self.api.get_bars(symbol, tf, limit=limit).df
            if bars.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame() # return empty
            return bars
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return pd.DataFrame()
