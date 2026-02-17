import json
import logging
from datetime import datetime, date
from config.settings import Config
import os

logger = logging.getLogger("TradingBot")

class RiskEngine:
    """
    Manages risk per trade and per day.
    Tracks state of daily trades and PnL in a JSON file (simple persistence for MVP).
    """

    STATE_FILE = "risk_state.json"

    def __init__(self, account_api_adapter):
        self.adapter = account_api_adapter
        self.state = self.load_state()

    def load_state(self):
        # Loads daily stats from JSON. If file missing or old date, reset.
        today_str = date.today().isoformat()
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE, 'r') as f:
                    data = json.load(f)
                    if data.get('date') == today_str:
                        return data
            except Exception as e:
                logger.error(f"Error loading risk state: {e}")
        
        # New day or first run
        return {
            "date": today_str,
            "trades_count": 0,
            "daily_loss": 0.0,
            "starting_balance": self.get_balance()
        }

    def save_state(self):
        try:
            with open(self.STATE_FILE, 'w') as f:
                json.dump(self.state, f)
        except Exception as e:
            logger.error(f"Error saving risk state: {e}")

    def get_balance(self):
        acct = self.adapter.get_account()
        return float(acct.equity) if acct else 0.0

    def check_trade(self, signal):
        """
        Validates if a trade can be executed based on risk rules.
        """
        if signal['signal'] == 'HOLD':
            return False, "Signal is HOLD"

        current_balance = self.get_balance()
        
        # 1. Check daily trade limit
        if self.state['trades_count'] >= Config.MAX_TRADES_PER_DAY:
            return False, "Max daily trades reached"

        # 2. Check daily loss limit
        # Calculate daily loss based on starting balance vs current balance
        # (Assuming simple PnL tracking for MVP based on account equity change)
        pnl = current_balance - self.state['starting_balance']
        daily_loss_pct = -pnl / self.state['starting_balance'] if self.state['starting_balance'] > 0 else 0

        if daily_loss_pct > Config.DAILY_STOP_LOSS_PCT:
            return False, f"Daily loss limit excessive ({daily_loss_pct:.2%})"

        # 3. Position Sizing
        # Max capital to risk per trade (position size)
        # The rule says "Max 5% del capital por posición". This is position sizing constraint.
        # We need to calculate size here or in executor. 
        # Usually risk engine dictates the max allowed size.
        
        max_position_value = current_balance * Config.MAX_CAPITAL_PER_TRADE_PCT
        
        # For this MVP, we will validate the trade is allowed and suggest size in USD.
        # The executor will then convert to shares based on price.
        
        return True, max_position_value

    def record_trade(self):
        """
        Call this after a trade is successfully executed.
        """
        self.state['trades_count'] += 1
        self.save_state()

