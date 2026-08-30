import os
from backtest_common.StrategyBase_cls import StrategyBase
from backtest_common import __backtestconfig__
"""
from TALibrary_cls import TALibrary as ta
from upstox_core.data_creators.TradeDataCreator_cls import TradeDataCreator
from datetime import datetime, timedelta
import pandas as pd
import pandas_ta as pta
import numpy as np
"""

class Strategy(StrategyBase):

    def __init__(self, strategy_id, broker):
        super().__init__(strategy_id, broker)
        self.history_data_raw_file_dir = __backtestconfig__.HISTORY_DATA_RAW_FILE_DIR
        self.exp_inst_scrip_master_file_dir = __backtestconfig__.EXP_INST_SCRIP_MASTER_FILE_DIR
        self.exp_contracts_nf_file_name = __backtestconfig__.EXP_INST_SCRIP_MASTER_NF_OPT_FILE
        self.exp_contracts_bnf_file_name = __backtestconfig__.EXP_INST_SCRIP_MASTER_BNF_OPT_FILE
        self.curr_inst_scrip_master_file_dir = __backtestconfig__.CURR_INST_SCRIP_MASTER_FILE_DIR
        self.curr_opt_contracts_nf_file_name = __backtestconfig__.CURR_INST_SCRIP_MASTER_NF_OPT_FILE
        self.curr_opt_contracts_bnf_file_name = __backtestconfig__.CURR_INST_SCRIP_MASTER_BNF_OPT_FILE
        self.expiries_file_dir = __backtestconfig__.EXPIRIES_FILE_DIR
        self.expiry_dates_nf_file = __backtestconfig__.EXPIRIES_NF_FILE
        self.expiry_dates_bnf_file = __backtestconfig__.EXPIRIES_BNF_FILE
        
        self.signal_file_dir = __backtestconfig__.SIGNAL_FILE_DIR
        self.signal_file_name = f"{self.strategy_id}_Signal_File.csv"
        self.signal_file = os.path.join(self.signal_file_dir, self.signal_file_name)
        self.trade_data_file_dir = __backtestconfig__.TRADE_DATA_FILE_DIR
        self.signal_trade_file_name = f"{self.strategy_id}_Signal_Trade_File.csv"
        self.signal_trade_file = os.path.join(self.trade_data_file_dir, self.signal_trade_file_name)
        self.signal_trade_details_zipfile_name = f"{self.strategy_id}_Signal_Trade_Details_File.zip"
        self.signal_trade_details_zipfile = os.path.join(self.trade_data_file_dir, self.signal_trade_details_zipfile_name)
        self.trade_data_details_dir = __backtestconfig__.TRADE_DATA_DETAILS_DIR

        self.df_hist_data = None
        self.df_expiry_dates = None
        self.signal_trades = None
        self.signal_trade_details = None
        self.signal_trade_details_files = None

    def create_signal_data_for_strategy(self):
        """ Calculates Indicators for each Strategy and Dataframe. """
        return

    def calculate_indicators(self):
        """ Calculates Indicators for each Strategy and Dataframe. """
        return

    def identify_entry_exit_feed_rows(self):
        """ Identifies entry and exit triggers for the strategy. """
        return

    def set_trade_instr_details(self):
        """ Sets the trade instrument for the strategy. """
        return

"""
    def create_signal_data_for_strategy(self):
        if self.strategy_id == "NIFTY_S01":
            history_data_file_name = f"Nifty_HistoryData_{self.__dict__.get('entry_interval_value')}m.csv"
            expiry_dates_file_name = self.expiry_dates_nf_file
            curr_contracts_file_name = self.curr_opt_contracts_nf_file_name

        elif self.strategy_id == "NIFTY_S02":
            history_data_file_name = f"Nifty_HistoryData_{self.__dict__.get('entry_interval_value')}m.csv"
            expiry_dates_file_name = self.expiry_dates_nf_file
            curr_contracts_file_name = self.curr_opt_contracts_nf_file_name

        elif self.strategy_id in ['NIFTY_S03']:
            history_data_file_name = f"Nifty_HistoryData_{self.__dict__.get('entry_interval_value')}m.csv"
            expiry_dates_file_name = self.expiry_dates_nf_file
            curr_contracts_file_name = self.curr_opt_contracts_nf_file_name

        elif self.strategy_id in ['NIFTY_S04']:
            history_data_file_name = f"Nifty_HistoryData_{self.__dict__.get('entry_interval_value')}m.csv"
            expiry_dates_file_name = self.expiry_dates_nf_file
            curr_contracts_file_name = self.curr_opt_contracts_nf_file_name

        elif self.strategy_id in ['NIFTY_S05']:
            history_data_file_name = f"Nifty_HistoryData_{self.__dict__.get('entry_interval_value')}m.csv"
            expiry_dates_file_name = self.expiry_dates_nf_file
            curr_contracts_file_name = self.curr_opt_contracts_nf_file_name

        elif self.strategy_id in ['NIFTY_S06']:
            history_data_file_name = f"Nifty_HistoryData_{self.__dict__.get('entry_interval_value')}m.csv"
            expiry_dates_file_name = self.expiry_dates_nf_file
            curr_contracts_file_name = self.curr_opt_contracts_nf_file_name

        history_data_raw_file = os.path.join(self.history_data_raw_file_dir, history_data_file_name)
        expiry_dates_file = os.path.join(self.expiries_file_dir, expiry_dates_file_name)
        curr_opt_contracts_file = os.path.join(self.curr_inst_scrip_master_file_dir, curr_contracts_file_name)

        self.df_hist_data = pd.read_csv(history_data_raw_file, dtype={'candle_sttime': str, 'open': float, 'high': float, 'low': float, 'close': float, 'vol': float})
        self.df_expiry_dates = pd.read_csv(expiry_dates_file, dtype={'expiry': str, 'weekly': bool, 'expiry_type': str})
        self.curr_opt_contracts = pd.read_csv(curr_opt_contracts_file, dtype={'exchange': str,'exchange_token': str, 'expiry': str, 'freeze_quantity': int, 'instrument_key': str, 'instrument_type': str, 'lot_size': int, 'minimum_lot': int, 'name': str, 'segment': str, 'strike_price': int, 'tick_size': int, 'trading_symbol': str, 'underlying_key': str, 'weekly': bool})

        candle_sttime_col_index = self.df_hist_data.columns.get_loc('candle_sttime')

        candle_date = pd.to_datetime(pd.to_datetime(self.df_hist_data['candle_sttime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%Y-%m-%d'), format='%Y-%m-%d')
        #candle_open_time = pd.to_datetime(pd.to_datetime(self.df_hist_data['candle_sttime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%H:%M:%S'), format='%H:%M:%S')

        self.df_hist_data.insert(loc=candle_sttime_col_index + 1, column='candle_date', value=candle_date)
        #self.df_hist_data.insert(loc=candle_sttime_col_index + 2, column='candle_open_time', value=candle_open_time)
        
        self.calculate_indicators()

        self.identify_entry_exit_feed_rows()

        self.set_trade_instr_details()

        with open(self.signal_file, "wt") as cfile:
            cfile.write(self.df_hist_data.to_csv(index=False, header=True))
        print(f"{str(datetime.now())} Finished writing Signal File after setting Strike, Expiry and Right for strategy_id {self.strategy_id}")
        #signal_file = ""
        if self.strategy_id == "NIFTY_S01":
            pass
        elif self.strategy_id == "NIFTY_S02":
            pass
        elif self.strategy_id in ['NIFTY_S03']:
            condition_trade = self.df_hist_data['is_entry_filter']
            df_buy_strike_contract_details = self.update_buy_strike_contracts_details(self.df_hist_data['buy_strike_expiry'])
            self.df_hist_data.loc[condition_trade, 'instrument_key'] = df_buy_strike_contract_details['instrument_key'].astype(str)
            self.df_hist_data.loc[condition_trade, 'trading_symbol'] = df_buy_strike_contract_details['trading_symbol'].astype(str)
            self.df_hist_data.loc[condition_trade, 'lot_size'] = df_buy_strike_contract_details['lot_size'].astype(int)
            self.df_hist_data['lot_size'] = self.df_hist_data['lot_size'].fillna(0).astype(int)
            self.df_hist_data.loc[condition_trade, 'freeze_quantity'] = df_buy_strike_contract_details['freeze_quantity'].astype(int)
            self.df_hist_data['freeze_quantity'] = self.df_hist_data['freeze_quantity'].fillna(0).astype(int)

        elif self.strategy_id in ['NIFTY_S04']:
            condition_trade = self.df_hist_data['is_entry_filter']
            df_buy_strike_contract_details = self.update_buy_strike_contracts_details(self.df_hist_data['buy_strike_expiry'])
            self.df_hist_data.loc[condition_trade, 'instrument_key'] = df_buy_strike_contract_details['instrument_key'].astype(str)
            self.df_hist_data.loc[condition_trade, 'trading_symbol'] = df_buy_strike_contract_details['trading_symbol'].astype(str)
            self.df_hist_data.loc[condition_trade, 'lot_size'] = df_buy_strike_contract_details['lot_size'].astype(int)
            self.df_hist_data['lot_size'] = self.df_hist_data['lot_size'].fillna(0).astype(int)
            self.df_hist_data.loc[condition_trade, 'freeze_quantity'] = df_buy_strike_contract_details['freeze_quantity'].astype(int)
            self.df_hist_data['freeze_quantity'] = self.df_hist_data['freeze_quantity'].fillna(0).astype(int)

        elif self.strategy_id in ['NIFTY_S05']:
            condition_trade = self.df_hist_data['is_entry_filter']
            df_buy_strike_contract_details = self.update_buy_strike_contracts_details(self.df_hist_data['buy_strike_expiry'])
            self.df_hist_data.loc[condition_trade, 'instrument_key'] = df_buy_strike_contract_details['instrument_key'].astype(str)
            self.df_hist_data.loc[condition_trade, 'trading_symbol'] = df_buy_strike_contract_details['trading_symbol'].astype(str)
            self.df_hist_data.loc[condition_trade, 'lot_size'] = df_buy_strike_contract_details['lot_size'].astype(int)
            self.df_hist_data['lot_size'] = self.df_hist_data['lot_size'].fillna(0).astype(int)
            self.df_hist_data.loc[condition_trade, 'freeze_quantity'] = df_buy_strike_contract_details['freeze_quantity'].astype(int)
            self.df_hist_data['freeze_quantity'] = self.df_hist_data['freeze_quantity'].fillna(0).astype(int)

        elif self.strategy_id in ['NIFTY_S06']:
            condition_trade = self.df_hist_data['is_entry_filter']
            df_buy_strike_contract_details = self.update_buy_strike_contracts_details(self.df_hist_data['buy_strike_expiry'])
            self.df_hist_data.loc[condition_trade, 'instrument_key'] = df_buy_strike_contract_details['instrument_key'].astype(str)
            self.df_hist_data.loc[condition_trade, 'trading_symbol'] = df_buy_strike_contract_details['trading_symbol'].astype(str)
            self.df_hist_data.loc[condition_trade, 'lot_size'] = df_buy_strike_contract_details['lot_size'].astype(int)
            self.df_hist_data['lot_size'] = self.df_hist_data['lot_size'].fillna(0).astype(int)
            self.df_hist_data.loc[condition_trade, 'freeze_quantity'] = df_buy_strike_contract_details['freeze_quantity'].astype(int)
            self.df_hist_data['freeze_quantity'] = self.df_hist_data['freeze_quantity'].fillna(0).astype(int)

        if self.strategy_id == "NIFTY_S01":
            pass
        elif self.strategy_id == "NIFTY_S02":
            pass
        elif self.strategy_id in ['NIFTY_S03']:
            self.df_hist_data.drop('buy_strike_contract_file', axis=1, inplace=True)
        elif self.strategy_id in ['NIFTY_S04']:
            self.df_hist_data.drop('buy_strike_contract_file', axis=1, inplace=True)
        elif self.strategy_id in ['NIFTY_S05']:
            self.df_hist_data.drop('buy_strike_contract_file', axis=1, inplace=True)
        elif self.strategy_id in ['NIFTY_S06']:
            self.df_hist_data.drop('buy_strike_contract_file', axis=1, inplace=True)

        self.df_hist_data.reset_index(drop=True, inplace=True)
        
        with open(self.signal_file, "wt") as cfile:
            cfile.write(self.df_hist_data.to_csv(index=False, header=True))
        print(f"{str(datetime.now())} Finished writing Signal File after Updating Buy Strike Instrument details for strategy_id {self.strategy_id}")
        
        self.df_hist_data = None
        self.df_expiry_dates = None
        self.curr_opt_contracts = None

        return

    # Calculate indicators for the DataFrame (Pandas Series) based on the interval and unit
    #@profile
    def calculate_indicators(self):

        print(f"{str(datetime.now())} Calculating indicators for strategy_id {self.strategy_id}")
        #for key, value in self.__dict__.items():
        #    print(f"Key: {key}, Value: {value}")

        if self.strategy_id == "NIFTY_S01":

            st_atr_length = self.__dict__.get('entry_st_atr_length')
            st_atr_factor = self.__dict__.get('entry_st_atr_factor')

            self.df_hist_data['st_val'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERT_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_dir'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTd_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_lb'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTl_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_ub'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTs_{st_atr_length}_{st_atr_factor}']).astype(float)

            #self.df_hist_data = self.df_hist_data.iloc[st_atr_length:]

        elif self.strategy_id == "NIFTY_S02":

            st_atr_length = self.__dict__.get('entry_st_atr_length')
            st_atr_factor = self.__dict__.get('entry_st_atr_factor')

            self.df_hist_data['st_val'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERT_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_dir'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTd_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_lb'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTl_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_ub'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTs_{st_atr_length}_{st_atr_factor}']).astype(float)

            #self.df_hist_data = self.df_hist_data.iloc[st_atr_length:]

        elif self.strategy_id in ['NIFTY_S03']:

            ema_length = self.__dict__.get('entry_trigger_ema_length')
            ema_source = self.__dict__.get('entry_trigger_ema_source')
            ema_ema_length = self.__dict__.get('entry_trigger_ema_ema_length')
            filter_st_atr_length = self.__dict__.get('entry_filter_st_atr_length')
            filter_st_atr_factor = self.__dict__.get('entry_filter_st_atr_factor')

            self.df_hist_data['ema_val'] = (pta.ema(self.df_hist_data[ema_source], length=ema_length)).astype(float)
            #self.df_hist_data = self.df_hist_data.iloc[ema_length:]
            self.df_hist_data['ema_ema_val'] = (pta.ema(self.df_hist_data['ema_val'], length=ema_ema_length)).astype(float)

            #self.df_hist_data = self.df_hist_data.iloc[ema_ema_length:]

            self.df_hist_data['st_val'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=filter_st_atr_length, multiplier=filter_st_atr_factor)[f'SUPERT_{filter_st_atr_length}_{filter_st_atr_factor}']).astype(float)
            self.df_hist_data['st_dir'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=filter_st_atr_length, multiplier=filter_st_atr_factor)[f'SUPERTd_{filter_st_atr_length}_{filter_st_atr_factor}']).astype(float)
            self.df_hist_data['st_lb'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=filter_st_atr_length, multiplier=filter_st_atr_factor)[f'SUPERTl_{filter_st_atr_length}_{filter_st_atr_factor}']).astype(float)
            self.df_hist_data['st_ub'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=filter_st_atr_length, multiplier=filter_st_atr_factor)[f'SUPERTs_{filter_st_atr_length}_{filter_st_atr_factor}']).astype(float)

            #self.df_hist_data = self.df_hist_data.iloc[filter_st_atr_length:]

        elif self.strategy_id in ['NIFTY_S04']:

            ema_length = self.__dict__.get('entry_trigger_ema_length')
            ema_source = self.__dict__.get('entry_trigger_ema_source')
            ema_ema_length = self.__dict__.get('entry_trigger_ema_ema_length')
            filter_st_atr_length = self.__dict__.get('entry_filter_st_atr_length')
            filter_st_atr_factor = self.__dict__.get('entry_filter_st_atr_factor')

            self.df_hist_data['ema_val'] = (pta.ema(self.df_hist_data[ema_source], length=ema_length)).astype(float)
            #self.df_hist_data = self.df_hist_data.iloc[ema_length:]
            self.df_hist_data['ema_ema_val'] = (pta.ema(self.df_hist_data['ema_val'], length=ema_ema_length)).astype(float)

            #self.df_hist_data = self.df_hist_data.iloc[ema_ema_length:]

            self.df_hist_data['st_val'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=filter_st_atr_length, multiplier=filter_st_atr_factor)[f'SUPERT_{filter_st_atr_length}_{filter_st_atr_factor}']).astype(float)
            self.df_hist_data['st_dir'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=filter_st_atr_length, multiplier=filter_st_atr_factor)[f'SUPERTd_{filter_st_atr_length}_{filter_st_atr_factor}']).astype(float)
            self.df_hist_data['st_lb'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=filter_st_atr_length, multiplier=filter_st_atr_factor)[f'SUPERTl_{filter_st_atr_length}_{filter_st_atr_factor}']).astype(float)
            self.df_hist_data['st_ub'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=filter_st_atr_length, multiplier=filter_st_atr_factor)[f'SUPERTs_{filter_st_atr_length}_{filter_st_atr_factor}']).astype(float)

            #self.df_hist_data = self.df_hist_data.iloc[filter_st_atr_length:]

        elif self.strategy_id in ['NIFTY_S05']:

            st_atr_length = self.__dict__.get('entry_trigger_st_atr_length')
            st_atr_factor = self.__dict__.get('entry_trigger_st_atr_factor')
            filter_ema_length = self.__dict__.get('entry_filter_ema_length')
            filter_ema_source = self.__dict__.get('entry_filter_ema_source')
            filter_ema_ema_length = self.__dict__.get('entry_filter_ema_ema_length')

            self.df_hist_data['st_val'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERT_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_dir'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTd_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_lb'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTl_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_ub'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTs_{st_atr_length}_{st_atr_factor}']).astype(float)

            #self.df_hist_data = self.df_hist_data.iloc[st_atr_length:]

            self.df_hist_data['ema_val'] = (pta.ema(self.df_hist_data[filter_ema_source], length=filter_ema_length)).astype(float)
            #self.df_hist_data = self.df_hist_data.iloc[filter_ema_length:]
            self.df_hist_data['ema_ema_val'] = (pta.ema(self.df_hist_data['ema_val'], length=filter_ema_ema_length)).astype(float)

            #self.df_hist_data = self.df_hist_data.iloc[filter_ema_ema_length:]

        elif self.strategy_id in ['NIFTY_S06']:

            st_atr_length = self.__dict__.get('entry_trigger_st_atr_length')
            st_atr_factor = self.__dict__.get('entry_trigger_st_atr_factor')
            filter_ema_length = self.__dict__.get('entry_filter_ema_length')
            filter_ema_source = self.__dict__.get('entry_filter_ema_source')
            filter_ema_ema_length = self.__dict__.get('entry_filter_ema_ema_length')

            self.df_hist_data['st_val'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERT_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_dir'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTd_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_lb'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTl_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_ub'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTs_{st_atr_length}_{st_atr_factor}']).astype(float)

            #self.df_hist_data = self.df_hist_data.iloc[st_atr_length:]

            self.df_hist_data['ema_val'] = (pta.ema(self.df_hist_data[filter_ema_source], length=filter_ema_length)).astype(float)
            #self.df_hist_data = self.df_hist_data.iloc[filter_ema_length:]
            self.df_hist_data['ema_ema_val'] = (pta.ema(self.df_hist_data['ema_val'], length=filter_ema_ema_length)).astype(float)

            #self.df_hist_data = self.df_hist_data.iloc[filter_ema_ema_length:]
        print(f"{str(datetime.now())} Finished Calculating Indicators for strategy_id {self.strategy_id}")
        return

    def identify_entry_exit_feed_rows(self):

        print(f"{str(datetime.now())} Identifying Entry Exit Feed rows for strategy_id {self.strategy_id}")
        #for key, value in self.__dict__.items():
        #    print(f"Key: {key}, Value: {value}")

        if self.strategy_id == "NIFTY_S01":

            # Initialize is_entry_trigger and is_exit_trigger with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_exit_trigger'] = False

            # Condition for is_entry_trigger: st_dir in previous row is 1 AND st_dir in row before previous is -1
            condition_entry = (self.df_hist_data['st_dir'].shift(1) == 1) & (self.df_hist_data['st_dir'].shift(2) == -1)
            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_exit_trigger: st_dir in previous row is -1 AND st_dir in row before previous is 1
            condition_exit = (self.df_hist_data['st_dir'].shift(1) == -1) & (self.df_hist_data['st_dir'].shift(2) == 1)
            self.df_hist_data.loc[condition_exit, 'is_exit_trigger'] = True

        elif self.strategy_id == "NIFTY_S02":

            # Initialize is_entry_trigger and is_exit_trigger with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_exit_trigger'] = False

            # Condition for is_entry_trigger: st_dir in previous row is -1 AND st_dir in row before previous is 1
            condition_entry = (self.df_hist_data['st_dir'].shift(1) == -1) & (self.df_hist_data['st_dir'].shift(2) == 1)
            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_exit_trigger: st_dir in previous row is 1 AND st_dir in row before previous is -1
            condition_exit = (self.df_hist_data['st_dir'].shift(1) == 1) & (self.df_hist_data['st_dir'].shift(2) == -1)
            self.df_hist_data.loc[condition_exit, 'is_exit_trigger'] = True

        elif self.strategy_id in ['NIFTY_S03']:

            strategy_entry_time = self.__dict__.get('entry_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_time = pd.to_datetime(strategy_entry_time, format='%H:%M:%S')
            strategy_entry_cutoff = self.__dict__.get('entry_cutoff')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_cut_off = pd.to_datetime(strategy_entry_cutoff, format='%H:%M:%S')

            # Initialize is_entry_trigger and is_entry_filter with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_entry_filter'] = False

            # Convert the Series of strings in YYYY-mm-dd HH:MM:SS format to datetime objects in HH:MM:SS format
            # Convert the datetime objects to strings in HH:MM:SS format and then convert them to datetime objects in HH:MM:SS format
            candle_open_time = pd.to_datetime(pd.to_datetime(self.df_hist_data['candle_sttime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%H:%M:%S'), format='%H:%M:%S')

            # Condition for is_entry_trigger: price crossed above ema_ema_val in previous row
            # and current candle open time >= strategy entry_time and < strategy entry_cut_off
            condition_entry = (self.df_hist_data['close'].shift(2) < self.df_hist_data['ema_ema_val'].shift(2)) & \
                (self.df_hist_data['close'].shift(1) > self.df_hist_data['ema_ema_val'].shift(1)) & \
                (candle_open_time >= entry_time) & \
                (candle_open_time < entry_cut_off)
                
            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_entry_filter: ema_ema_val in previous row > st_val in previous row and st_dir in previous row == 1
            condition_filter = (self.df_hist_data['ema_ema_val'].shift(1) > self.df_hist_data['st_val'].shift(1)) & (self.df_hist_data['st_dir'].shift(1) == 1.0) & condition_entry
            self.df_hist_data.loc[condition_filter, 'is_entry_filter'] = True

        elif self.strategy_id in ['NIFTY_S04']:

            strategy_entry_time = self.__dict__.get('entry_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_time = pd.to_datetime(strategy_entry_time, format='%H:%M:%S')
            strategy_entry_cutoff = self.__dict__.get('entry_cutoff')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_cut_off = pd.to_datetime(strategy_entry_cutoff, format='%H:%M:%S')

            # Initialize is_entry_trigger and is_entry_filter with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_entry_filter'] = False

            # Convert the Series of strings in YYYY-mm-dd HH:MM:SS format to datetime objects in HH:MM:SS format
            # Convert the datetime objects to strings in HH:MM:SS format and then convert them to datetime objects in HH:MM:SS format
            candle_open_time = pd.to_datetime(pd.to_datetime(self.df_hist_data['candle_sttime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%H:%M:%S'), format='%H:%M:%S')

            # Condition for is_entry_trigger: price crossed below ema_ema_val in previous row
            # and current candle open time >= strategy entry_time and < strategy entry_cut_off
            condition_entry = (self.df_hist_data['close'].shift(2) > self.df_hist_data['ema_ema_val'].shift(2)) & \
                (self.df_hist_data['close'].shift(1) < self.df_hist_data['ema_ema_val'].shift(1)) & \
                (candle_open_time >= entry_time) & \
                (candle_open_time < entry_cut_off)
                
            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_entry_filter: ema_ema_val in previous row < st_val in previous row and st_dir in previous row == -1
            condition_filter = (self.df_hist_data['ema_ema_val'].shift(1) < self.df_hist_data['st_val'].shift(1)) & (self.df_hist_data['st_dir'].shift(1) == -1.0) & condition_entry
            self.df_hist_data.loc[condition_filter, 'is_entry_filter'] = True

        elif self.strategy_id in ['NIFTY_S05']:

            strategy_entry_time = self.__dict__.get('entry_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_time = pd.to_datetime(strategy_entry_time, format='%H:%M:%S')
            strategy_entry_cutoff = self.__dict__.get('entry_cutoff')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_cut_off = pd.to_datetime(strategy_entry_cutoff, format='%H:%M:%S')

            # Initialize is_entry_trigger and is_entry_filter with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_entry_filter'] = False

            # Convert the Series of strings in YYYY-mm-dd HH:MM:SS format to datetime objects in HH:MM:SS format
            # Convert the datetime objects to strings in HH:MM:SS format and then convert them to datetime objects in HH:MM:SS format
            candle_open_time = pd.to_datetime(pd.to_datetime(self.df_hist_data['candle_sttime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%H:%M:%S'), format='%H:%M:%S')

            # Condition for is_entry_trigger: close crossed above supertrend in previous row
            # and current candle open time >= strategy entry_time and < strategy entry_cut_off
            condition_entry = (self.df_hist_data['st_dir'].shift(1) == 1) & \
                (self.df_hist_data['st_dir'].shift(2) == -1) & \
                (candle_open_time >= entry_time) & \
                (candle_open_time < entry_cut_off)
            
            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_entry_filter: st_val in row before previous row > ema_ema_val in row before previous row
            condition_filter = (self.df_hist_data['st_val'].shift(2) > self.df_hist_data['ema_ema_val'].shift(2)) & condition_entry
            self.df_hist_data.loc[condition_filter, 'is_entry_filter'] = True

        elif self.strategy_id in ['NIFTY_S06']:

            strategy_entry_time = self.__dict__.get('entry_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_time = pd.to_datetime(strategy_entry_time, format='%H:%M:%S')
            strategy_entry_cutoff = self.__dict__.get('entry_cutoff')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_cut_off = pd.to_datetime(strategy_entry_cutoff, format='%H:%M:%S')

            # Initialize is_entry_trigger and is_entry_filter with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_entry_filter'] = False

            # Convert the Series of strings in YYYY-mm-dd HH:MM:SS format to datetime objects in HH:MM:SS format
            # Convert the datetime objects to strings in HH:MM:SS format and then convert them to datetime objects in HH:MM:SS format
            candle_open_time = pd.to_datetime(pd.to_datetime(self.df_hist_data['candle_sttime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%H:%M:%S'), format='%H:%M:%S')

            # Condition for is_entry_trigger: close > ema_ema_val in row before previous row and close < ema_ema_val in previous row
            # and current candle open time >= strategy entry_time and < strategy entry_cut_off
            condition_entry = (self.df_hist_data['st_dir'].shift(1) == -1) & \
                (self.df_hist_data['st_dir'].shift(2) == 1) & \
                (candle_open_time >= entry_time) & \
                (candle_open_time < entry_cut_off)
            
            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_entry_filter: st_val in row before previous row < ema_ema_val in row before previous row
            condition_filter = (self.df_hist_data['st_val'].shift(2) < self.df_hist_data['ema_ema_val'].shift(2)) & condition_entry
            self.df_hist_data.loc[condition_filter, 'is_entry_filter'] = True

        print(f"{str(datetime.now())} Finished Identifying Entry Condition Rows for strategy_id {self.strategy_id}")
        return

    def set_trade_instr_details(self):

        print(f"{str(datetime.now())} Setting trade instrument details for strategy_id {self.strategy_id}")
        #for key, value in self.__dict__.items():
        #    print(f"Key: {key}, Value: {value}")

        if self.strategy_id == "NIFTY_S01":

            # Initialize is_entry_trigger and is_exit_trigger with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_exit_trigger'] = False

            # Condition for is_entry_trigger: st_dir in previous row is 1 AND st_dir in row before previous is -1
            condition_entry = (self.df_hist_data['st_dir'].shift(1) == 1) & (self.df_hist_data['st_dir'].shift(2) == -1)
            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_exit_trigger: st_dir in previous row is -1 AND st_dir in row before previous is 1
            condition_exit = (self.df_hist_data['st_dir'].shift(1) == -1) & (self.df_hist_data['st_dir'].shift(2) == 1)
            self.df_hist_data.loc[condition_exit, 'is_exit_trigger'] = True

        elif self.strategy_id == "NIFTY_S02":

            # Initialize is_entry_trigger and is_exit_trigger with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_exit_trigger'] = False

            # Condition for is_entry_trigger: st_dir in previous row is -1 AND st_dir in row before previous is 1
            condition_entry = (self.df_hist_data['st_dir'].shift(1) == -1) & (self.df_hist_data['st_dir'].shift(2) == 1)
            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_exit_trigger: st_dir in previous row is 1 AND st_dir in row before previous is -1
            condition_exit = (self.df_hist_data['st_dir'].shift(1) == 1) & (self.df_hist_data['st_dir'].shift(2) == -1)
            self.df_hist_data.loc[condition_exit, 'is_exit_trigger'] = True

        elif self.strategy_id in ['NIFTY_S03']:

            strike_multiple = self.__dict__.get('strike_multiple')
            buy_strike_offset = self.__dict__.get('buy_strike_offset')
            buy_strike_right = self.__dict__.get('buy_strike_right')

            condition_trade = self.df_hist_data['is_entry_filter']
            self.df_hist_data.loc[condition_trade, 'buy_strike'] = (self.get_buy_strike(self.df_hist_data['open'], strike_multiple, buy_strike_offset, buy_strike_right)).astype(int)
            self.df_hist_data['buy_strike'] = self.df_hist_data['buy_strike'].fillna(0).astype(int)

            df_buy_strike_expiry_details = self.get_buy_strike_expiry_details(self.df_hist_data['candle_sttime'], weekly=True)
            condition_trade = self.df_hist_data['is_entry_filter']
            self.df_hist_data.loc[condition_trade, 'buy_strike_expiry'] = df_buy_strike_expiry_details['buy_strike_expiry'].astype(str)
            self.df_hist_data.loc[condition_trade, 'buy_strike_expiry_type'] = df_buy_strike_expiry_details['buy_strike_expiry_type'].astype(str)
            self.df_hist_data.loc[condition_trade, 'buy_strike_contract_file'] = df_buy_strike_expiry_details['buy_strike_contract_file'].astype(str)
            self.df_hist_data.loc[condition_trade, 'buy_strike_right'] = buy_strike_right

            self.df_hist_data.reset_index(drop=True, inplace=True)

        elif self.strategy_id in ['NIFTY_S04']:

            strike_multiple = self.__dict__.get('strike_multiple')
            buy_strike_offset = self.__dict__.get('buy_strike_offset')
            buy_strike_right = self.__dict__.get('buy_strike_right')

            condition_trade = self.df_hist_data['is_entry_filter']
            self.df_hist_data.loc[condition_trade, 'buy_strike'] = (self.get_buy_strike(self.df_hist_data['open'], strike_multiple, buy_strike_offset, buy_strike_right)).astype(int)
            self.df_hist_data['buy_strike'] = self.df_hist_data['buy_strike'].fillna(0).astype(int)

            df_buy_strike_expiry_details = self.get_buy_strike_expiry_details(self.df_hist_data['candle_sttime'], weekly=True)
            condition_trade = self.df_hist_data['is_entry_filter']
            self.df_hist_data.loc[condition_trade, 'buy_strike_expiry'] = df_buy_strike_expiry_details['buy_strike_expiry'].astype(str)
            self.df_hist_data.loc[condition_trade, 'buy_strike_expiry_type'] = df_buy_strike_expiry_details['buy_strike_expiry_type'].astype(str)
            self.df_hist_data.loc[condition_trade, 'buy_strike_contract_file'] = df_buy_strike_expiry_details['buy_strike_contract_file'].astype(str)
            self.df_hist_data.loc[condition_trade, 'buy_strike_right'] = buy_strike_right

            self.df_hist_data.reset_index(drop=True, inplace=True)

        elif self.strategy_id in ['NIFTY_S05']:

            strike_multiple = self.__dict__.get('strike_multiple')
            buy_strike_offset = self.__dict__.get('buy_strike_offset')
            buy_strike_right = self.__dict__.get('buy_strike_right')

            condition_trade = self.df_hist_data['is_entry_filter']
            self.df_hist_data.loc[condition_trade, 'buy_strike'] = (self.get_buy_strike(self.df_hist_data['open'], strike_multiple, buy_strike_offset, buy_strike_right)).astype(int)
            self.df_hist_data['buy_strike'] = self.df_hist_data['buy_strike'].fillna(0).astype(int)

            df_buy_strike_expiry_details = self.get_buy_strike_expiry_details(self.df_hist_data['candle_sttime'], weekly=True)
            condition_trade = self.df_hist_data['is_entry_filter']
            self.df_hist_data.loc[condition_trade, 'buy_strike_expiry'] = df_buy_strike_expiry_details['buy_strike_expiry'].astype(str)
            self.df_hist_data.loc[condition_trade, 'buy_strike_expiry_type'] = df_buy_strike_expiry_details['buy_strike_expiry_type'].astype(str)
            self.df_hist_data.loc[condition_trade, 'buy_strike_contract_file'] = df_buy_strike_expiry_details['buy_strike_contract_file'].astype(str)
            self.df_hist_data.loc[condition_trade, 'buy_strike_right'] = buy_strike_right

            self.df_hist_data.reset_index(drop=True, inplace=True)

        elif self.strategy_id in ['NIFTY_S06']:

            strike_multiple = self.__dict__.get('strike_multiple')
            buy_strike_offset = self.__dict__.get('buy_strike_offset')
            buy_strike_right = self.__dict__.get('buy_strike_right')

            condition_trade = self.df_hist_data['is_entry_filter']
            self.df_hist_data.loc[condition_trade, 'buy_strike'] = (self.get_buy_strike(self.df_hist_data['open'], strike_multiple, buy_strike_offset, buy_strike_right)).astype(int)
            self.df_hist_data['buy_strike'] = self.df_hist_data['buy_strike'].fillna(0).astype(int)

            df_buy_strike_expiry_details = self.get_buy_strike_expiry_details(self.df_hist_data['candle_sttime'], weekly=True)
            condition_trade = self.df_hist_data['is_entry_filter']
            self.df_hist_data.loc[condition_trade, 'buy_strike_expiry'] = df_buy_strike_expiry_details['buy_strike_expiry'].astype(str)
            self.df_hist_data.loc[condition_trade, 'buy_strike_expiry_type'] = df_buy_strike_expiry_details['buy_strike_expiry_type'].astype(str)
            self.df_hist_data.loc[condition_trade, 'buy_strike_contract_file'] = df_buy_strike_expiry_details['buy_strike_contract_file'].astype(str)
            self.df_hist_data.loc[condition_trade, 'buy_strike_right'] = buy_strike_right

            self.df_hist_data.reset_index(drop=True, inplace=True)

        print(f"{str(datetime.now())} Finished setting Trade Instrument Details for strategy_id {self.strategy_id}")
        return

    # Finds a multiple of 50 or 100 that greater or less than a given number depending on right (PE or CE)
    def get_buy_strike(self, open_series, strike_multiple, buy_strike_offset, buy_strike_right) -> pd.Series:
        if buy_strike_right == "PE":
            remainder = open_series % strike_multiple
            zero_rem_indices = remainder[remainder == 0].index
            nozero_rem_indices = remainder[remainder != 0].index
            strike_series = pd.Series(index=open_series.index, dtype=int)
            strike_series.loc[zero_rem_indices] = pd.Series((open_series[zero_rem_indices] + strike_multiple + buy_strike_offset).astype(int))
            strike_series.loc[nozero_rem_indices] = pd.Series(((open_series[nozero_rem_indices] // strike_multiple + 1) * strike_multiple + buy_strike_offset).astype(int))
            strike_series.sort_index()

        elif buy_strike_right == "CE":
            remainder = open_series % strike_multiple
            zero_rem_indices = remainder[remainder == 0].index
            nozero_rem_indices = remainder[remainder != 0].index
            strike_series = pd.Series(index=open_series.index, dtype=int)
            strike_series.loc[zero_rem_indices] = pd.Series((open_series[zero_rem_indices] - strike_multiple - buy_strike_offset).astype(int))
            strike_series.loc[nozero_rem_indices] = pd.Series(((open_series[nozero_rem_indices] // strike_multiple) * strike_multiple - buy_strike_offset).astype(int))
            strike_series.sort_index()

        return strike_series

    # Finds the applicable expiry date, expiry type (expired or Current) and expiry contracts file
    def get_buy_strike_expiry_details(self, candle_sttime_series, weekly=True) -> pd.DataFrame:

        expiry_dates_series = pd.to_datetime(pd.to_datetime(self.df_expiry_dates['expiry']).dt.strftime('%Y-%m-%d'), format='%Y-%m-%d')
        exp_type_series = self.df_expiry_dates['expiry_type']
        first_avl_date = (pd.to_datetime(expiry_dates_series).min()).date()
        print(f"{str(datetime.now())} First Date for which Expiry Data is available: {first_avl_date}")
        print(f"{str(datetime.now())} First Date from which Historical Data shoud be analysed: {first_avl_date - timedelta(days=7)}")

        hist_data_datetime_series = pd.to_datetime(pd.to_datetime(candle_sttime_series).dt.strftime('%Y-%m-%d'), format='%Y-%m-%d')

        exp_data_not_avl_indices = candle_sttime_series[hist_data_datetime_series.dt.date <= (first_avl_date - timedelta(days=7))].index
        self.df_hist_data.drop(labels=exp_data_not_avl_indices, inplace=True)
        hist_data_datetime_series.drop(labels=exp_data_not_avl_indices, inplace=True)
        candle_sttime_series.drop(labels=exp_data_not_avl_indices, inplace=True)
        print(f"{str(datetime.now())} First Date for which Expiry Data is available: {first_avl_date}")
        exp_data_avl_indices = candle_sttime_series[hist_data_datetime_series.dt.date > (first_avl_date - timedelta(days=7))].index

        expiry_series = pd.Series(index=candle_sttime_series.index, dtype=str)
        expiry_type_series = pd.Series(index=candle_sttime_series.index, dtype=str)
        expiry_file_series = pd.Series(index=candle_sttime_series.index, dtype=str)
        #expiry_series[exp_data_not_avl_indices] = pd.Series(pd.to_datetime(candle_sttime_series[exp_data_not_avl_indices]).dt.strftime('%Y-%m-%d'))
        
        expiry_series.loc[exp_data_avl_indices] = pd.Series(pd.to_datetime(candle_sttime_series[exp_data_avl_indices]).dt.strftime('%Y-%m-%d'))

        # Initialize an empty Series to store the results
        next_greater_dates_series = pd.Series(index=exp_data_avl_indices, dtype='datetime64[ns]')
        expiry_type_avl_series = pd.Series(index=exp_data_avl_indices, dtype=str)
        expiry_file_avl_series = pd.Series(index=exp_data_avl_indices, dtype=str)

        for i, val in expiry_series[exp_data_avl_indices].items():
            greater_than_val = expiry_dates_series[expiry_dates_series > val]
            
            if not greater_than_val.empty:
                next_greater_dates_series.loc[i] = greater_than_val.min()
                expiry_type_avl_series.loc[i] = exp_type_series[expiry_dates_series == greater_than_val.min()].values
                if self.strategy_id == "NIFTY_S01":

                    curr_contracts_file = os.path.join(self.curr_inst_scrip_master_file_dir, curr_contracts_file_name)
                elif self.strategy_id == "NIFTY_S02":

                    curr_contracts_file_name = self.curr_opt_contracts_nf_file_name
                elif self.strategy_id in ['NIFTY_S03']:
                    exp_date_str = pd.to_datetime(greater_than_val.min(), format='%Y-%m-%d').strftime('%Y-%m-%d')
                    exp_contracts_file_name = self.exp_contracts_nf_file_name.replace("EXPIRY", exp_date_str)
                    curr_contracts_file_name = self.curr_opt_contracts_nf_file_name
                    exp_contracts_file = os.path.join(self.exp_inst_scrip_master_file_dir, exp_contracts_file_name)
                    curr_contracts_file = os.path.join(self.curr_inst_scrip_master_file_dir, curr_contracts_file_name)

                    if os.path.exists(exp_contracts_file):
                        expiry_file_avl_series[i] = exp_contracts_file
                    elif os.path.exists(curr_contracts_file):
                        expiry_file_avl_series[i] = curr_contracts_file
                    else:
                        expiry_file_avl_series.loc[i] = pd.NA

                elif self.strategy_id in ['NIFTY_S04']:
                    exp_date_str = pd.to_datetime(greater_than_val.min(), format='%Y-%m-%d').strftime('%Y-%m-%d')
                    exp_contracts_file_name = self.exp_contracts_nf_file_name.replace("EXPIRY", exp_date_str)
                    curr_contracts_file_name = self.curr_opt_contracts_nf_file_name
                    exp_contracts_file = os.path.join(self.exp_inst_scrip_master_file_dir, exp_contracts_file_name)
                    curr_contracts_file = os.path.join(self.curr_inst_scrip_master_file_dir, curr_contracts_file_name)

                    if os.path.exists(exp_contracts_file):
                        expiry_file_avl_series[i] = exp_contracts_file
                    elif os.path.exists(curr_contracts_file):
                        expiry_file_avl_series[i] = curr_contracts_file
                    else:
                        expiry_file_avl_series.loc[i] = pd.NA

                elif self.strategy_id in ['NIFTY_S05']:
                    exp_date_str = pd.to_datetime(greater_than_val.min(), format='%Y-%m-%d').strftime('%Y-%m-%d')
                    exp_contracts_file_name = self.exp_contracts_nf_file_name.replace("EXPIRY", exp_date_str)
                    curr_contracts_file_name = self.curr_opt_contracts_nf_file_name
                    exp_contracts_file = os.path.join(self.exp_inst_scrip_master_file_dir, exp_contracts_file_name)
                    curr_contracts_file = os.path.join(self.curr_inst_scrip_master_file_dir, curr_contracts_file_name)

                    if os.path.exists(exp_contracts_file):
                        expiry_file_avl_series[i] = exp_contracts_file
                    elif os.path.exists(curr_contracts_file):
                        expiry_file_avl_series[i] = curr_contracts_file
                    else:
                        expiry_file_avl_series.loc[i] = pd.NA

                elif self.strategy_id in ['NIFTY_S06']:
                    exp_date_str = pd.to_datetime(greater_than_val.min(), format='%Y-%m-%d').strftime('%Y-%m-%d')
                    exp_contracts_file_name = self.exp_contracts_nf_file_name.replace("EXPIRY", exp_date_str)
                    curr_contracts_file_name = self.curr_opt_contracts_nf_file_name
                    exp_contracts_file = os.path.join(self.exp_inst_scrip_master_file_dir, exp_contracts_file_name)
                    curr_contracts_file = os.path.join(self.curr_inst_scrip_master_file_dir, curr_contracts_file_name)

                    if os.path.exists(exp_contracts_file):
                        expiry_file_avl_series[i] = exp_contracts_file
                    elif os.path.exists(curr_contracts_file):
                        expiry_file_avl_series[i] = curr_contracts_file
                    else:
                        expiry_file_avl_series.loc[i] = pd.NA

            else:
                next_greater_dates_series.loc[i] = pd.NaT
                expiry_type_avl_series.loc[i] = pd.NA
                expiry_file_avl_series.loc[i] = pd.NA
        
        expiry_series.loc[exp_data_avl_indices] = pd.Series(pd.to_datetime(next_greater_dates_series).dt.strftime('%Y-%m-%d'))
        expiry_type_series.loc[exp_data_avl_indices] = expiry_type_avl_series
        expiry_file_series.loc[exp_data_avl_indices] = expiry_file_avl_series
        expiry_series.sort_index()
        expiry_type_series.sort_index()
        expiry_file_series.sort_index()
        df_buy_strike_expiry_details = pd.DataFrame({
            'buy_strike_expiry': expiry_series,
            'buy_strike_expiry_type': expiry_type_series,
            'buy_strike_contract_file': expiry_file_series
        })
        return df_buy_strike_expiry_details

    def update_buy_strike_contracts_details(self, signal_buy_strike_series) -> pd.DataFrame:

        df_buy_strike_contract_details = pd.DataFrame()

        inst_key_series = pd.Series(index=signal_buy_strike_series.index, dtype=str)
        trading_symbol_series = pd.Series(index=signal_buy_strike_series.index, dtype=str)
        lot_size_series = pd.Series(index=signal_buy_strike_series.index, dtype=int)
        freeze_quantity_series = pd.Series(index=signal_buy_strike_series.index, dtype=int)        

        no_trade_indices = signal_buy_strike_series[signal_buy_strike_series.isna()].index
        trade_indices = signal_buy_strike_series[~signal_buy_strike_series.isna()].index
        
        inst_key_series.loc[no_trade_indices] = ""
        trading_symbol_series.loc[no_trade_indices] = ""
        lot_size_series.loc[no_trade_indices] = 0
        freeze_quantity_series.loc[no_trade_indices] = 0

        if self.strategy_id == "NIFTY_S01":

            curr_contracts_file_name = self.curr_opt_contracts_nf_file_name
        elif self.strategy_id == "NIFTY_S02":

            curr_contracts_file_name = self.curr_opt_contracts_nf_file_name
        elif self.strategy_id in ['NIFTY_S03']:

            df_signal_file = pd.read_csv(self.signal_file, usecols=['buy_strike', 'buy_strike_expiry', 'buy_strike_right', 'buy_strike_contract_file'], dtype={'buy_strike': int, 'buy_strike_expiry': str, 'buy_strike_right': str, 'buy_strike_contract_file': str})
            df_signal_file_trade = df_signal_file.iloc[trade_indices]

            for i, row in df_signal_file_trade.iterrows():
                buy_strike = row['buy_strike']
                buy_strike_expiry = row['buy_strike_expiry']
                buy_strike_right = row['buy_strike_right']

                df_contract_file = pd.read_csv(row['buy_strike_contract_file'], usecols=['expiry', 'instrument_key', 'instrument_type', 'lot_size', 'freeze_quantity', 'strike_price', 'trading_symbol'], dtype={'expiry': str, 'instrument_key': str, 'instrument_type': str, 'lot_size': int, 'freeze_quantity': int, 'strike_price': int, 'trading_symbol': str})
                #df_contract_file = pd.read_csv(row['buy_strike_contract_file'], usecols=['expiry', 'instrument_key', 'instrument_type', 'strike_price', 'trading_symbol'], dtype={'expiry': str, 'instrument_key': str, 'instrument_type': str, 'strike_price': int, 'trading_symbol': str})

                df_contract_file_filtered = df_contract_file[
                    (df_contract_file['strike_price'] == buy_strike) &
                    (df_contract_file['expiry'] == buy_strike_expiry) &
                    (df_contract_file['instrument_type'] == buy_strike_right)
                ]
                inst_key_series[i] = df_contract_file_filtered['instrument_key'].values
                trading_symbol_series[i] = df_contract_file_filtered['trading_symbol'].values
                lot_size_series[i] = df_contract_file_filtered['lot_size'].values
                freeze_quantity_series[i] = df_contract_file_filtered['freeze_quantity'].values

        elif self.strategy_id in ['NIFTY_S04']:

            df_signal_file = pd.read_csv(self.signal_file, usecols=['buy_strike', 'buy_strike_expiry', 'buy_strike_right', 'buy_strike_contract_file'], dtype={'buy_strike': int, 'buy_strike_expiry': str, 'buy_strike_right': str, 'buy_strike_contract_file': str})
            df_signal_file_trade = df_signal_file.iloc[trade_indices]

            for i, row in df_signal_file_trade.iterrows():
                buy_strike = row['buy_strike']
                buy_strike_expiry = row['buy_strike_expiry']
                buy_strike_right = row['buy_strike_right']

                df_contract_file = pd.read_csv(row['buy_strike_contract_file'], usecols=['expiry', 'instrument_key', 'instrument_type', 'lot_size', 'freeze_quantity', 'strike_price', 'trading_symbol'], dtype={'expiry': str, 'instrument_key': str, 'instrument_type': str, 'lot_size': int, 'freeze_quantity': int, 'strike_price': int, 'trading_symbol': str})
                #df_contract_file = pd.read_csv(row['buy_strike_contract_file'], usecols=['expiry', 'instrument_key', 'instrument_type', 'strike_price', 'trading_symbol'], dtype={'expiry': str, 'instrument_key': str, 'instrument_type': str, 'strike_price': int, 'trading_symbol': str})

                df_contract_file_filtered = df_contract_file[
                    (df_contract_file['strike_price'] == buy_strike) &
                    (df_contract_file['expiry'] == buy_strike_expiry) &
                    (df_contract_file['instrument_type'] == buy_strike_right)
                ]
                inst_key_series[i] = df_contract_file_filtered['instrument_key'].values
                trading_symbol_series[i] = df_contract_file_filtered['trading_symbol'].values
                lot_size_series[i] = df_contract_file_filtered['lot_size'].values
                freeze_quantity_series[i] = df_contract_file_filtered['freeze_quantity'].values

        elif self.strategy_id in ['NIFTY_S05']:

            df_signal_file = pd.read_csv(self.signal_file, usecols=['buy_strike', 'buy_strike_expiry', 'buy_strike_right', 'buy_strike_contract_file'], dtype={'buy_strike': int, 'buy_strike_expiry': str, 'buy_strike_right': str, 'buy_strike_contract_file': str})
            df_signal_file_trade = df_signal_file.iloc[trade_indices]

            for i, row in df_signal_file_trade.iterrows():
                buy_strike = row['buy_strike']
                buy_strike_expiry = row['buy_strike_expiry']
                buy_strike_right = row['buy_strike_right']

                df_contract_file = pd.read_csv(row['buy_strike_contract_file'], usecols=['expiry', 'instrument_key', 'instrument_type', 'lot_size', 'freeze_quantity', 'strike_price', 'trading_symbol'], dtype={'expiry': str, 'instrument_key': str, 'instrument_type': str, 'lot_size': int, 'freeze_quantity': int, 'strike_price': int, 'trading_symbol': str})
                #df_contract_file = pd.read_csv(row['buy_strike_contract_file'], usecols=['expiry', 'instrument_key', 'instrument_type', 'strike_price', 'trading_symbol'], dtype={'expiry': str, 'instrument_key': str, 'instrument_type': str, 'strike_price': int, 'trading_symbol': str})

                df_contract_file_filtered = df_contract_file[
                    (df_contract_file['strike_price'] == buy_strike) &
                    (df_contract_file['expiry'] == buy_strike_expiry) &
                    (df_contract_file['instrument_type'] == buy_strike_right)
                ]
                inst_key_series[i] = df_contract_file_filtered['instrument_key'].values
                trading_symbol_series[i] = df_contract_file_filtered['trading_symbol'].values
                lot_size_series[i] = df_contract_file_filtered['lot_size'].values
                freeze_quantity_series[i] = df_contract_file_filtered['freeze_quantity'].values

        elif self.strategy_id in ['NIFTY_S06']:

            df_signal_file = pd.read_csv(self.signal_file, usecols=['buy_strike', 'buy_strike_expiry', 'buy_strike_right', 'buy_strike_contract_file'], dtype={'buy_strike': int, 'buy_strike_expiry': str, 'buy_strike_right': str, 'buy_strike_contract_file': str})
            df_signal_file_trade = df_signal_file.iloc[trade_indices]

            for i, row in df_signal_file_trade.iterrows():
                buy_strike = row['buy_strike']
                buy_strike_expiry = row['buy_strike_expiry']
                buy_strike_right = row['buy_strike_right']

                df_contract_file = pd.read_csv(row['buy_strike_contract_file'], usecols=['expiry', 'instrument_key', 'instrument_type', 'lot_size', 'freeze_quantity', 'strike_price', 'trading_symbol'], dtype={'expiry': str, 'instrument_key': str, 'instrument_type': str, 'lot_size': int, 'freeze_quantity': int, 'strike_price': int, 'trading_symbol': str})
                #df_contract_file = pd.read_csv(row['buy_strike_contract_file'], usecols=['expiry', 'instrument_key', 'instrument_type', 'strike_price', 'trading_symbol'], dtype={'expiry': str, 'instrument_key': str, 'instrument_type': str, 'strike_price': int, 'trading_symbol': str})

                df_contract_file_filtered = df_contract_file[
                    (df_contract_file['strike_price'] == buy_strike) &
                    (df_contract_file['expiry'] == buy_strike_expiry) &
                    (df_contract_file['instrument_type'] == buy_strike_right)
                ]
                inst_key_series[i] = df_contract_file_filtered['instrument_key'].values
                trading_symbol_series[i] = df_contract_file_filtered['trading_symbol'].values
                lot_size_series[i] = df_contract_file_filtered['lot_size'].values
                freeze_quantity_series[i] = df_contract_file_filtered['freeze_quantity'].values

        df_buy_strike_contract_details = pd.DataFrame({
            'instrument_key': inst_key_series,
            'trading_symbol': trading_symbol_series,
            'lot_size': lot_size_series,
            'freeze_quantity': freeze_quantity_series
        })

        print(f"{str(datetime.now())} Finished updating Contract Details for strategy_id {self.strategy_id}")
        return df_buy_strike_contract_details
"""
