from backtest_common import __strategyconfig__
import logging
from abc import ABCMeta, abstractmethod

class StrategyBase(object):

    __metaclass__ = ABCMeta

    def __init__(self, strategy_id, broker):
        self.strategy_id = strategy_id
        self.broker = broker
        # Create and configure logger
        self.logger = logging.getLogger(f"logs/{strategy_id}.log")
        self.logger.addHandler(logging.FileHandler(f"logs/{strategy_id}.log", mode='a'))
        self.logger.setLevel(logging.INFO)
        self.strategy_file_dat_extn = __strategyconfig__.STRATEGY_FILE_DAT_EXTN
        self.strategy_config_file_dir = __strategyconfig__.STRATEGY_CONFIG_DIR

    @abstractmethod
    def create_signal_data_for_strategy(self):
        """ Calculates Indicators for each Strategy and Dataframe. """
        raise NotImplementedError("Should implement create_signal_strategy()")

    @abstractmethod
    def calculate_indicators(self):
        """ Calculates Indicators for each Strategy and Dataframe. """
        raise NotImplementedError("Should implement calculate_indicators()")

    @abstractmethod
    def identify_entry_exit_feed_rows(self):
        """ Identifies entry and exit triggers for the strategy. """
        raise NotImplementedError("Should implement identify_entry_exit_feedrows()")

    @abstractmethod
    def set_trade_instr_details(self):
        """ Sets the trade instrument for the strategy. """
        raise NotImplementedError("Should implement set_trade_instr_details()")
