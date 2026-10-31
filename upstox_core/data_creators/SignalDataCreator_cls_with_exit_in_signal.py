import os
from datetime import datetime, timedelta
import logging
import pandas as pd
import pandas_ta as pta
import numpy as np
from backtest_common import __backtestconfig__
from backtest_common.TALibrary_cls import TALibrary

# Create and configure logger
signal_data_creator_logger = logging.getLogger("logs/signal_data_creator.log")
signal_data_creator_logger.addHandler(logging.FileHandler("logs/signal_data_creator.log", mode='a'))
signal_data_creator_logger.setLevel(logging.INFO)

class SignalDataCreator:

    def __init__(self, broker, logger=signal_data_creator_logger):
        self.broker=broker
        self.logger=logger
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

        self.df_hist_data = None
        self.df_expiry_dates = None
        self.df_signal_details = None

    def create_signal_data_for_strategy(self, strategy_obj):
        strategy_id = strategy_obj.strategy_id
        self.talib = TALibrary(self.broker)
        
        signal_file = strategy_obj.signal_file

        if strategy_id == "NIFTY_S01":
            history_data_file_name = f"Nifty_HistoryData_{strategy_obj.__dict__.get('entry_interval_value')}m.csv"
            expiry_dates_file_name = self.expiry_dates_nf_file
            curr_contracts_file_name = self.curr_opt_contracts_nf_file_name

        elif strategy_id == "NIFTY_S02":
            history_data_file_name = f"Nifty_HistoryData_{strategy_obj.__dict__.get('entry_interval_value')}m.csv"
            expiry_dates_file_name = self.expiry_dates_nf_file
            curr_contracts_file_name = self.curr_opt_contracts_nf_file_name

        elif strategy_id in ['NIFTY_S03', 'NIFTY_S04', 'NIFTY_S05', 'NIFTY_S06', 'NIFTY_S07', 'NIFTY_S08', 'NIFTY_S09', 'NIFTY_S10']:
            history_data_file_name = f"Nifty_HistoryData_{strategy_obj.__dict__.get('entry_interval_value')}m.csv"
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

        self.df_hist_data.insert(loc=candle_sttime_col_index + 1, column='candle_date', value=candle_date)
        
        self.calculate_indicators(strategy_obj)

        self.identify_entry_signal_rows(strategy_obj)

        self.set_trade_instr_details(strategy_obj)

        with open(signal_file, "wt", newline='') as cfile:
            cfile.write(self.df_hist_data.to_csv(index=False, header=True))
        print(f"{str(datetime.now())} Finished writing Signal File {signal_file} after setting Strike, Expiry and Right for strategy_id {strategy_id}")

        if strategy_id == "NIFTY_S01":
            pass
        elif strategy_id == "NIFTY_S02":
            pass
        elif strategy_id in ['NIFTY_S03', 'NIFTY_S04', 'NIFTY_S05', 'NIFTY_S06', 'NIFTY_S07', 'NIFTY_S08', 'NIFTY_S09', 'NIFTY_S10']:
            condition_trade = self.df_hist_data['is_entry_filter']
            df_buy_strike_contract_details = self.update_buy_strike_contracts_details(self.df_hist_data['buy_strike_expiry'], strategy_obj)
            self.df_hist_data.loc[condition_trade, 'instrument_key'] = df_buy_strike_contract_details['instrument_key'].astype(str)
            self.df_hist_data.loc[condition_trade, 'trading_symbol'] = df_buy_strike_contract_details['trading_symbol'].astype(str)
            self.df_hist_data.loc[condition_trade, 'lot_size'] = df_buy_strike_contract_details['lot_size'].astype(int)
            self.df_hist_data['lot_size'] = self.df_hist_data['lot_size'].fillna(0).astype(int)
            self.df_hist_data.loc[condition_trade, 'freeze_quantity'] = df_buy_strike_contract_details['freeze_quantity'].astype(int)
            self.df_hist_data['freeze_quantity'] = self.df_hist_data['freeze_quantity'].fillna(0).astype(int)
            self.df_hist_data.drop('buy_strike_contract_file', axis=1, inplace=True)

        self.df_hist_data.reset_index(drop=True, inplace=True)
        
        with open(signal_file, "wt", newline='') as cfile:
            cfile.write(self.df_hist_data.to_csv(index=False, header=True))
        print(f"{str(datetime.now())} Finished writing Signal File {signal_file} after Updating Buy Strike Instrument details for strategy_id {strategy_id}")
        
        self.df_hist_data = None
        self.df_expiry_dates = None
        self.curr_opt_contracts = None

        """
        for key, value in strategy_obj.__dict__.items():
            print(f"{str(datetime.now())} key={key} value={value}")
        """

        return

    # Calculate indicators for the DataFrame (Pandas Series) based on the interval and unit
    #@profile
    def calculate_indicators(self, strategy_obj):

        strategy_id = strategy_obj.strategy_id
        print(f"{str(datetime.now())} Calculating indicators for strategy_id {strategy_id}")
        #for key, value in strategy_obj.__dict__.items():
        #    print(f"Key: {key}, Value: {value}")

        if strategy_id == "NIFTY_S01":

            st_atr_length = strategy_obj.__dict__.get('entry_st_atr_length')
            st_atr_factor = strategy_obj.__dict__.get('entry_st_atr_factor')

            self.df_hist_data['st_val'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERT_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_dir'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTd_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_lb'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTl_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_ub'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTs_{st_atr_length}_{st_atr_factor}']).astype(float)

            #self.df_hist_data = self.df_hist_data.iloc[st_atr_length:]

        elif strategy_id == "NIFTY_S02":

            st_atr_length = strategy_obj.__dict__.get('entry_st_atr_length')
            st_atr_factor = strategy_obj.__dict__.get('entry_st_atr_factor')

            self.df_hist_data['st_val'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERT_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_dir'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTd_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_lb'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTl_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_ub'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTs_{st_atr_length}_{st_atr_factor}']).astype(float)

            #self.df_hist_data = self.df_hist_data.iloc[st_atr_length:]

        elif strategy_id in ['NIFTY_S03']:

            entry_trigger_3mHL_multiplier = strategy_obj.__dict__.get('entry_trigger_3mHL_multiplier')
            entry_trigger_3mHL_source = strategy_obj.__dict__.get('entry_trigger_3mHL_source')
            filter_ema_length = strategy_obj.__dict__.get('entry_filter_ema_length')
            filter_ema_source = strategy_obj.__dict__.get('entry_filter_ema_source')
            filter_rma_ema_length = strategy_obj.__dict__.get('entry_filter_rma_ema_length')
            exit_atr_length = strategy_obj.__dict__.get('exit_atr_length')
            exit_atr_multipier = strategy_obj.__dict__.get('exit_atr_multipier')
            close_col_index = self.df_hist_data.columns.get_loc('close')

            first_3m_high = self.df_hist_data.groupby('candle_date')[entry_trigger_3mHL_source].transform(lambda x: x.iloc[0])
            first_3m_high_extended = first_3m_high * entry_trigger_3mHL_multiplier

            self.df_hist_data.insert(loc=close_col_index + 1, column='first_3m_high_extended', value=first_3m_high_extended)
            self.df_hist_data.insert(loc=close_col_index + 2, column='first_3m_high', value=first_3m_high)

            #self.df_hist_data[f'first_3m_high'] = self.df_hist_data.groupby('candle_date')[entry_trigger_3mHL_source].transform(lambda x: x.iloc[0])
            #self.df_hist_data[f'first_3m_high_extended'] = (self.df_hist_data.groupby('candle_date')[entry_trigger_3mHL_source].transform(lambda x: x.iloc[0]))*entry_trigger_3mHL_multiplier

            self.df_hist_data['ema_val'] = (pta.ema(self.df_hist_data[filter_ema_source], length=filter_ema_length)).astype(float)

            self.df_hist_data['rma_ema_val'] = (pta.rma(self.df_hist_data['ema_val'], length=filter_rma_ema_length)).astype(float)

            #self.df_hist_data['st_val'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=filter_st_atr_length, multiplier=filter_st_atr_factor)[f'SUPERT_{filter_st_atr_length}_{filter_st_atr_factor}']).astype(float)

            self.df_hist_data['atr_val'] = pta.atr(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=exit_atr_length, mamode='rma').astype(float)

            self.df_hist_data['atr_tsl_long'] = (self.df_hist_data['high'].shift(1) - (self.df_hist_data['atr_val'] * exit_atr_multipier)).astype(float)
            self.df_hist_data['atr_tsl_short'] = (self.df_hist_data['low'].shift(1) + (self.df_hist_data['atr_val'] * exit_atr_multipier)).astype(float)

        elif strategy_id in ['NIFTY_S04']:

            entry_trigger_3mHL_multiplier = strategy_obj.__dict__.get('entry_trigger_3mHL_multiplier')
            entry_trigger_3mHL_source = strategy_obj.__dict__.get('entry_trigger_3mHL_source')
            filter_ema_length = strategy_obj.__dict__.get('entry_filter_ema_length')
            filter_ema_source = strategy_obj.__dict__.get('entry_filter_ema_source')
            filter_rma_ema_length = strategy_obj.__dict__.get('entry_filter_rma_ema_length')
            exit_atr_length = strategy_obj.__dict__.get('exit_atr_length')
            exit_atr_multipier = strategy_obj.__dict__.get('exit_atr_multipier')

            close_col_index = self.df_hist_data.columns.get_loc('close')

            first_3m_low = self.df_hist_data.groupby('candle_date')[entry_trigger_3mHL_source].transform(lambda x: x.iloc[0])
            first_3m_low_extended = first_3m_low * entry_trigger_3mHL_multiplier

            self.df_hist_data.insert(loc=close_col_index + 1, column='first_3m_low_extended', value=first_3m_low_extended)
            self.df_hist_data.insert(loc=close_col_index + 2, column='first_3m_low', value=first_3m_low)

            #self.df_hist_data[f'first_3m_low'] = self.df_hist_data.groupby('candle_date')[entry_trigger_3mHL_source].transform(lambda x: x.iloc[0])
            #self.df_hist_data[f'first_3m_low_extended'] = (self.df_hist_data.groupby('candle_date')[entry_trigger_3mHL_source].transform(lambda x: x.iloc[0]))*entry_trigger_3mHL_multiplier

            self.df_hist_data['ema_val'] = (pta.ema(self.df_hist_data[filter_ema_source], length=filter_ema_length)).astype(float)

            self.df_hist_data['rma_ema_val'] = (pta.rma(self.df_hist_data['ema_val'], length=filter_rma_ema_length)).astype(float)

            #self.df_hist_data['st_val'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=filter_st_atr_length, multiplier=filter_st_atr_factor)[f'SUPERT_{filter_st_atr_length}_{filter_st_atr_factor}']).astype(float)

            self.df_hist_data['atr_val'] = pta.atr(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=exit_atr_length, mamode='rma').astype(float)

            self.df_hist_data['atr_tsl_long'] = (self.df_hist_data['high'].shift(1) - (self.df_hist_data['atr_val'] * exit_atr_multipier)).astype(float)
            self.df_hist_data['atr_tsl_short'] = (self.df_hist_data['low'].shift(1) + (self.df_hist_data['atr_val'] * exit_atr_multipier)).astype(float)

        elif strategy_id in ['NIFTY_S05']:

            entry_trigger_3mHL_multiplier = strategy_obj.__dict__.get('entry_trigger_3mHL_multiplier')
            entry_trigger_3mHL_source = strategy_obj.__dict__.get('entry_trigger_3mHL_source')
            entry_trigger_gma_length = strategy_obj.__dict__.get('entry_trigger_gma_length')
            entry_trigger_gma_ema_length = strategy_obj.__dict__.get('entry_trigger_gma_ema_length')
            entry_trigger_gma_adaptive = strategy_obj.__dict__.get('entry_trigger_gma_adaptive')
            entry_trigger_gma_volatility_period = strategy_obj.__dict__.get('entry_trigger_gma_volatility_period')
            entry_trigger_gma_source = strategy_obj.__dict__.get('entry_trigger_gma_source')
            filter_ema_length = strategy_obj.__dict__.get('entry_filter_ema_length')
            filter_ema_source = strategy_obj.__dict__.get('entry_filter_ema_source')
            filter_rma_ema_length = strategy_obj.__dict__.get('entry_filter_rma_ema_length')
            exit_atr_length = strategy_obj.__dict__.get('exit_atr_length')
            exit_atr_multipier = strategy_obj.__dict__.get('exit_atr_multipier')

            self.df_hist_data[f'gma_val'] = self.talib.calc_gaussian_ma(self.df_hist_data[entry_trigger_gma_source], length=entry_trigger_gma_length, ema_length=entry_trigger_gma_ema_length, adaptive=entry_trigger_gma_adaptive, volatility_period=entry_trigger_gma_volatility_period, standard_deviation_override=1.0)

            close_col_index = self.df_hist_data.columns.get_loc('close')

            first_3m_high = self.df_hist_data.groupby('candle_date')[entry_trigger_3mHL_source].transform(lambda x: x.iloc[0])
            first_3m_high_extended = first_3m_high * entry_trigger_3mHL_multiplier

            self.df_hist_data.insert(loc=close_col_index + 1, column='first_3m_high_extended', value=first_3m_high_extended)
            self.df_hist_data.insert(loc=close_col_index + 2, column='first_3m_high', value=first_3m_high)

            self.df_hist_data['ema_val'] = (pta.ema(self.df_hist_data[filter_ema_source], length=filter_ema_length)).astype(float)

            self.df_hist_data['rma_ema_val'] = (pta.rma(self.df_hist_data['ema_val'], length=filter_rma_ema_length)).astype(float)

            #self.df_hist_data['st_val'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=filter_st_atr_length, multiplier=filter_st_atr_factor)[f'SUPERT_{filter_st_atr_length}_{filter_st_atr_factor}']).astype(float)

            self.df_hist_data['atr_val'] = pta.atr(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=exit_atr_length, mamode='rma').astype(float)

            self.df_hist_data['atr_tsl_long'] = (self.df_hist_data['high'].shift(1) - (self.df_hist_data['atr_val'] * exit_atr_multipier)).astype(float)
            self.df_hist_data['atr_tsl_short'] = (self.df_hist_data['low'].shift(1) + (self.df_hist_data['atr_val'] * exit_atr_multipier)).astype(float)

        elif strategy_id in ['NIFTY_S06']:

            entry_trigger_3mHL_multiplier = strategy_obj.__dict__.get('entry_trigger_3mHL_multiplier')
            entry_trigger_3mHL_source = strategy_obj.__dict__.get('entry_trigger_3mHL_source')
            entry_trigger_gma_length = strategy_obj.__dict__.get('entry_trigger_gma_length')
            entry_trigger_gma_ema_length = strategy_obj.__dict__.get('entry_trigger_gma_ema_length')
            entry_trigger_gma_adaptive = strategy_obj.__dict__.get('entry_trigger_gma_adaptive')
            entry_trigger_gma_volatility_period = strategy_obj.__dict__.get('entry_trigger_gma_volatility_period')
            entry_trigger_gma_source = strategy_obj.__dict__.get('entry_trigger_gma_source')
            filter_ema_length = strategy_obj.__dict__.get('entry_filter_ema_length')
            filter_ema_source = strategy_obj.__dict__.get('entry_filter_ema_source')
            filter_rma_ema_length = strategy_obj.__dict__.get('entry_filter_rma_ema_length')
            exit_atr_length = strategy_obj.__dict__.get('exit_atr_length')
            exit_atr_multipier = strategy_obj.__dict__.get('exit_atr_multipier')

            self.df_hist_data[f'gma_val'] = self.talib.calc_gaussian_ma(self.df_hist_data[entry_trigger_gma_source], length=entry_trigger_gma_length, ema_length=entry_trigger_gma_ema_length, adaptive=entry_trigger_gma_adaptive, volatility_period=entry_trigger_gma_volatility_period, standard_deviation_override=1.0)

            close_col_index = self.df_hist_data.columns.get_loc('close')

            first_3m_low = self.df_hist_data.groupby('candle_date')[entry_trigger_3mHL_source].transform(lambda x: x.iloc[0])
            first_3m_low_extended = first_3m_low * entry_trigger_3mHL_multiplier

            self.df_hist_data.insert(loc=close_col_index + 1, column='first_3m_low_extended', value=first_3m_low_extended)
            self.df_hist_data.insert(loc=close_col_index + 2, column='first_3m_low', value=first_3m_low)

            self.df_hist_data['ema_val'] = (pta.ema(self.df_hist_data[filter_ema_source], length=filter_ema_length)).astype(float)

            self.df_hist_data['rma_ema_val'] = (pta.rma(self.df_hist_data['ema_val'], length=filter_rma_ema_length)).astype(float)

            #self.df_hist_data['st_val'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=filter_st_atr_length, multiplier=filter_st_atr_factor)[f'SUPERT_{filter_st_atr_length}_{filter_st_atr_factor}']).astype(float)

            self.df_hist_data['atr_val'] = pta.atr(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=exit_atr_length, mamode='rma').astype(float)

            self.df_hist_data['atr_tsl_long'] = (self.df_hist_data['high'].shift(1) - (self.df_hist_data['atr_val'] * exit_atr_multipier)).astype(float)
            self.df_hist_data['atr_tsl_short'] = (self.df_hist_data['low'].shift(1) + (self.df_hist_data['atr_val'] * exit_atr_multipier)).astype(float)

        elif strategy_id in ['NIFTY_S07']:

            entry_trigger_ema_length = strategy_obj.__dict__.get('entry_trigger_ema_length')
            entry_trigger_ema_source = strategy_obj.__dict__.get('entry_trigger_ema_source')
            entry_trigger_rma_ema_length = strategy_obj.__dict__.get('entry_trigger_rma_ema_length')
            filter_ema_length = strategy_obj.__dict__.get('entry_filter_ema_length')
            filter_ema_source = strategy_obj.__dict__.get('entry_filter_ema_source')
            exit_atr_length = strategy_obj.__dict__.get('exit_atr_length')
            exit_atr_multipier = strategy_obj.__dict__.get('exit_atr_multipier')
            close_col_index = self.df_hist_data.columns.get_loc('close')

            self.df_hist_data['ema_val'] = (pta.ema(self.df_hist_data[filter_ema_source], length=filter_ema_length)).astype(float)

            #self.df_hist_data['rma_ema_val'] = (pta.rma(self.df_hist_data['ema_val'], length=filter_rma_ema_length)).astype(float)
            rma_3m = (pta.ema(self.df_hist_data['ema_val'], length=entry_trigger_rma_ema_length)).astype(float)
            self.df_hist_data.insert(loc=close_col_index + 1, column='rma_ema_val', value=rma_3m)

            filter_ema = (pta.ema(self.df_hist_data[filter_ema_source], length=filter_ema_length)).astype(float)
            self.df_hist_data.insert(loc=close_col_index + 2, column='filter_ema_val', value=filter_ema)

            self.df_hist_data['atr_val'] = pta.atr(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=exit_atr_length, mamode='rma').astype(float)

            self.df_hist_data['atr_tsl_long'] = (self.df_hist_data['high'].shift(1) - (self.df_hist_data['atr_val'] * exit_atr_multipier)).astype(float)

        elif strategy_id in ['NIFTY_S08']:

            entry_trigger_ema_length = strategy_obj.__dict__.get('entry_trigger_ema_length')
            entry_trigger_ema_source = strategy_obj.__dict__.get('entry_trigger_ema_source')
            entry_trigger_rma_ema_length = strategy_obj.__dict__.get('entry_trigger_rma_ema_length')
            filter_ema_length = strategy_obj.__dict__.get('entry_filter_ema_length')
            filter_ema_source = strategy_obj.__dict__.get('entry_filter_ema_source')
            exit_atr_length = strategy_obj.__dict__.get('exit_atr_length')
            exit_atr_multipier = strategy_obj.__dict__.get('exit_atr_multipier')
            close_col_index = self.df_hist_data.columns.get_loc('close')

            self.df_hist_data['ema_val'] = (pta.ema(self.df_hist_data[filter_ema_source], length=filter_ema_length)).astype(float)

            #self.df_hist_data['rma_ema_val'] = (pta.rma(self.df_hist_data['ema_val'], length=filter_rma_ema_length)).astype(float)
            rma_3m = (pta.ema(self.df_hist_data['ema_val'], length=entry_trigger_rma_ema_length)).astype(float)
            self.df_hist_data.insert(loc=close_col_index + 1, column='rma_ema_val', value=rma_3m)

            filter_ema = (pta.ema(self.df_hist_data[filter_ema_source], length=filter_ema_length)).astype(float)
            self.df_hist_data.insert(loc=close_col_index + 2, column='filter_ema_val', value=filter_ema)

            self.df_hist_data['atr_val'] = pta.atr(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=exit_atr_length, mamode='rma').astype(float)

            self.df_hist_data['atr_tsl_short'] = (self.df_hist_data['low'].shift(1) + (self.df_hist_data['atr_val'] * exit_atr_multipier)).astype(float)

        elif strategy_id in ['NIFTY_S09']:

            st_atr_length = strategy_obj.__dict__.get('entry_trigger_st_atr_length')
            st_atr_factor = strategy_obj.__dict__.get('entry_trigger_st_atr_factor')
            filter_ema_length = strategy_obj.__dict__.get('entry_filter_ema_length')
            filter_ema_source = strategy_obj.__dict__.get('entry_filter_ema_source')
            filter_rma_ema_length = strategy_obj.__dict__.get('entry_filter_rma_ema_length')

            self.df_hist_data['st_val'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERT_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_dir'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTd_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_lb'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTl_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_ub'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTs_{st_atr_length}_{st_atr_factor}']).astype(float)

            self.df_hist_data['ema_val'] = (pta.ema(self.df_hist_data[filter_ema_source], length=filter_ema_length)).astype(float)

            self.df_hist_data['rma_ema_val'] = (pta.ema(self.df_hist_data['ema_val'], length=filter_rma_ema_length)).astype(float)

        elif strategy_id in ['NIFTY_S10']:

            st_atr_length = strategy_obj.__dict__.get('entry_trigger_st_atr_length')
            st_atr_factor = strategy_obj.__dict__.get('entry_trigger_st_atr_factor')
            filter_ema_length = strategy_obj.__dict__.get('entry_filter_ema_length')
            filter_ema_source = strategy_obj.__dict__.get('entry_filter_ema_source')
            filter_rma_ema_length = strategy_obj.__dict__.get('entry_filter_rma_ema_length')

            self.df_hist_data['st_val'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERT_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_dir'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTd_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_lb'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTl_{st_atr_length}_{st_atr_factor}']).astype(float)
            self.df_hist_data['st_ub'] = (pta.supertrend(self.df_hist_data['high'], self.df_hist_data['low'], self.df_hist_data['close'], length=st_atr_length, multiplier=st_atr_factor)[f'SUPERTs_{st_atr_length}_{st_atr_factor}']).astype(float)

            self.df_hist_data['ema_val'] = (pta.ema(self.df_hist_data[filter_ema_source], length=filter_ema_length)).astype(float)

            self.df_hist_data['rma_ema_val'] = (pta.ema(self.df_hist_data['ema_val'], length=filter_rma_ema_length)).astype(float)

        print(f"{str(datetime.now())} Finished Calculating Indicators for strategy_id {strategy_id}")
        return

    def identify_entry_signal_rows(self, strategy_obj):

        strategy_id = strategy_obj.strategy_id
        print(f"{str(datetime.now())} Identifying Entry Signal rows for strategy_id {strategy_id}")
        #for key, value in strategy_obj.__dict__.items():
        #    print(f"Key: {key}, Value: {value}")

        if strategy_id == "NIFTY_S01":

            # Initialize is_entry_trigger and is_exit_trigger with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_exit_trigger'] = False

            # Condition for is_entry_trigger: st_dir in previous row is 1 AND st_dir in row before previous is -1
            condition_entry = (self.df_hist_data['st_dir'].shift(1) == 1) & (self.df_hist_data['st_dir'].shift(2) == -1)
            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_exit_trigger: st_dir in previous row is -1 AND st_dir in row before previous is 1
            condition_exit = (self.df_hist_data['st_dir'].shift(1) == -1) & (self.df_hist_data['st_dir'].shift(2) == 1)
            self.df_hist_data.loc[condition_exit, 'is_exit_trigger'] = True

        elif strategy_id == "NIFTY_S02":

            # Initialize is_entry_trigger and is_exit_trigger with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_exit_trigger'] = False

            # Condition for is_entry_trigger: st_dir in previous row is -1 AND st_dir in row before previous is 1
            condition_entry = (self.df_hist_data['st_dir'].shift(1) == -1) & (self.df_hist_data['st_dir'].shift(2) == 1)
            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_exit_trigger: st_dir in previous row is 1 AND st_dir in row before previous is -1
            condition_exit = (self.df_hist_data['st_dir'].shift(1) == 1) & (self.df_hist_data['st_dir'].shift(2) == -1)
            self.df_hist_data.loc[condition_exit, 'is_exit_trigger'] = True

        elif strategy_id in ['NIFTY_S03']:

            strategy_entry_time = strategy_obj.__dict__.get('entry_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_time = pd.to_datetime(strategy_entry_time, format='%H:%M:%S')
            strategy_entry_cutoff = strategy_obj.__dict__.get('entry_cutoff')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_cut_off = pd.to_datetime(strategy_entry_cutoff, format='%H:%M:%S')
            strategy_exit_time = strategy_obj.__dict__.get('exit_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            exit_time = pd.to_datetime(strategy_exit_time, format='%H:%M:%S')
            strategy_entry_filter_ema = strategy_obj.__dict__.get('entry_filter_ema')

            # Initialize is_entry_trigger and is_entry_filter with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_entry_filter'] = False
            self.df_hist_data['is_exit_trigger'] = False
            close_col_index = self.df_hist_data.columns.get_loc('close')
            entry_candle_low = np.nan
            is_trade_open = np.nan
            self.df_hist_data.insert(loc=close_col_index + 3, column='entry_candle_low', value=entry_candle_low)
            self.df_hist_data.insert(loc=close_col_index + 4, column='is_trade_open', value=is_trade_open)

            # Convert the Series of strings in YYYY-mm-dd HH:MM:SS format to datetime objects in HH:MM:SS format
            # Convert the datetime objects to strings in HH:MM:SS format and then convert them to datetime objects in HH:MM:SS format
            candle_open_time = pd.to_datetime(pd.to_datetime(self.df_hist_data['candle_sttime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%H:%M:%S'), format='%H:%M:%S')

            # Condition for is_entry_trigger: 3 min price closed above first 3 min candle close * multiplier in previous row
            # and current candle open time >= strategy entry_time and < strategy entry_cut_off
            condition_entry = (
                                (self.df_hist_data['close'].shift(2) <= self.df_hist_data['first_3m_high_extended'].shift(2)) & \
                                (self.df_hist_data['close'].shift(1) > self.df_hist_data['first_3m_high_extended'].shift(1))
                            ) & \
                            (self.df_hist_data['close'] > self.df_hist_data['low'].shift(1)) & \
                            (candle_open_time >= entry_time) & (candle_open_time < entry_cut_off)

            self.df_hist_data['entry_candle_low'] = self.df_hist_data.groupby('candle_date')['low'].shift(1).where(condition_entry)
            self.df_hist_data['entry_candle_low'] = self.df_hist_data.groupby('candle_date')['entry_candle_low'].ffill()

            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_entry_filter if it is configured to True: rma_ema_val in previous row > st_val in previous row and st_dir in previous row == 1
            # else set filter condition to entry condition 
            if strategy_entry_filter_ema:
                # condition_filter = condition_entry
                # Evaluate filter condition
                #condition_filter = ((self.df_hist_data['close'] > self.df_hist_data['rma_ema_val']) | (self.df_hist_data['close'] > self.df_hist_data['st_val'])) & \
                #                condition_entry
                condition_filter = (self.df_hist_data['close'] > self.df_hist_data['rma_ema_val']) & condition_entry
            else:
                condition_filter = condition_entry
            
            self.df_hist_data.loc[condition_filter, 'is_entry_filter'] = True
            self.df_hist_data.loc[condition_filter, 'is_trade_open'] = float(True)

            # Condition for is_exit_trigger: close in row before previous row >= entry candle low AND close in previous row < entry candle low
            """
            condition_exit = (
                                ((self.df_hist_data['close'].shift(2) >= self.df_hist_data['first_3m_high_extended'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) < self.df_hist_data['first_3m_high_extended'].shift(1))) | \
                                ((self.df_hist_data['close'].shift(2) >= self.df_hist_data['entry_candle_low'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) < self.df_hist_data['entry_candle_low'].shift(1))) | \
                                (candle_open_time >= exit_time)
                            )
            """
            
            # Condition for is_exit_trigger: close in row before previous row >= atr trailing stop loss AND close in previous row < atr trailing stop loss
            condition_exit = (
                                ((self.df_hist_data['close'].shift(2) >= self.df_hist_data['atr_tsl_long'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) < self.df_hist_data['atr_tsl_long'].shift(2))) | \
                                (candle_open_time >= exit_time)
                            )
            self.df_hist_data.loc[condition_exit, 'is_exit_trigger'] = True
            self.df_hist_data.loc[condition_exit, 'is_trade_open'] = float(False)

            self.df_hist_data['is_trade_open'] = self.df_hist_data['is_trade_open'].ffill().fillna(False)
            self.df_hist_data['is_trade_open'] = self.df_hist_data['is_trade_open'].astype(bool)

        elif strategy_id in ['NIFTY_S04']:

            strategy_entry_time = strategy_obj.__dict__.get('entry_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_time = pd.to_datetime(strategy_entry_time, format='%H:%M:%S')
            strategy_entry_cutoff = strategy_obj.__dict__.get('entry_cutoff')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_cut_off = pd.to_datetime(strategy_entry_cutoff, format='%H:%M:%S')
            strategy_exit_time = strategy_obj.__dict__.get('exit_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            exit_time = pd.to_datetime(strategy_exit_time, format='%H:%M:%S')
            strategy_entry_filter_ema = strategy_obj.__dict__.get('entry_filter_ema')

            # Initialize is_entry_trigger and is_entry_filter with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_entry_filter'] = False
            self.df_hist_data['is_exit_trigger'] = False
            close_col_index = self.df_hist_data.columns.get_loc('close')
            entry_candle_high = np.nan
            is_trade_open = np.nan
            self.df_hist_data.insert(loc=close_col_index + 3, column='entry_candle_high', value=entry_candle_high)
            self.df_hist_data.insert(loc=close_col_index + 4, column='is_trade_open', value=is_trade_open)

            # Convert the Series of strings in YYYY-mm-dd HH:MM:SS format to datetime objects in HH:MM:SS format
            # Convert the datetime objects to strings in HH:MM:SS format and then convert them to datetime objects in HH:MM:SS format
            candle_open_time = pd.to_datetime(pd.to_datetime(self.df_hist_data['candle_sttime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%H:%M:%S'), format='%H:%M:%S')

            # Condition for is_entry_trigger: price crossed below rma_ema_val in previous row
            # and current candle open time >= strategy entry_time and < strategy entry_cut_off
            condition_entry = (
                                (self.df_hist_data['close'].shift(2) >= self.df_hist_data['first_3m_low_extended'].shift(2)) & \
                                (self.df_hist_data['close'].shift(1) < self.df_hist_data['first_3m_low_extended'].shift(1))
                            ) & \
                            (self.df_hist_data['close'] < self.df_hist_data['high'].shift(1)) & \
                            (candle_open_time >= entry_time) & (candle_open_time < entry_cut_off)

            self.df_hist_data['entry_candle_high'] = self.df_hist_data.groupby('candle_date')['high'].shift(1).where(condition_entry)
            self.df_hist_data['entry_candle_high'] = self.df_hist_data.groupby('candle_date')['entry_candle_high'].ffill()

            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_entry_filter if it is configured to True: rma_ema_val in previous row > st_val in previous row and st_dir in previous row == 1
            # else set filter condition to entry condition 
            if strategy_entry_filter_ema:
                # condition_filter = condition_entry
                # Evaluate filter condition
                #condition_filter = ((self.df_hist_data['close'] < self.df_hist_data['rma_ema_val']) | (self.df_hist_data['close'] < self.df_hist_data['st_val'])) & \
                #                condition_entry
                condition_filter = (self.df_hist_data['close'] < self.df_hist_data['rma_ema_val']) & condition_entry
            else:
                condition_filter = condition_entry
            
            self.df_hist_data.loc[condition_filter, 'is_entry_filter'] = True
            self.df_hist_data.loc[condition_filter, 'is_trade_open'] = float(True)

            # Condition for is_exit_trigger: close in row before previous row <= entry candle high AND close in previous row > entry candle high
            """
            condition_exit = (
                                ((self.df_hist_data['close'].shift(2) <= self.df_hist_data['first_3m_low_extended'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) > self.df_hist_data['first_3m_low_extended'].shift(1))) | \
                                ((self.df_hist_data['close'].shift(2) <= self.df_hist_data['entry_candle_high'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) > self.df_hist_data['entry_candle_high'].shift(1))) | \
                                (candle_open_time >= exit_time)
                            )

            """

            # Condition for is_exit_trigger: close in row before previous row <= atr trailing stop loss AND close in previous row < atr trailing stop loss
            condition_exit = (
                                ((self.df_hist_data['close'].shift(2) <= self.df_hist_data['atr_tsl_short'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) > self.df_hist_data['atr_tsl_short'].shift(2))) | \
                                (candle_open_time >= exit_time)
                            )

            self.df_hist_data.loc[condition_exit, 'is_exit_trigger'] = True
            self.df_hist_data.loc[condition_exit, 'is_trade_open'] = float(False)

            self.df_hist_data['is_trade_open'] = self.df_hist_data['is_trade_open'].ffill().fillna(False)
            self.df_hist_data['is_trade_open'] = self.df_hist_data['is_trade_open'].astype(bool)

        elif strategy_id in ['NIFTY_S05']:

            strategy_entry_time = strategy_obj.__dict__.get('entry_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_time = pd.to_datetime(strategy_entry_time, format='%H:%M:%S')
            strategy_entry_cutoff = strategy_obj.__dict__.get('entry_cutoff')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_cut_off = pd.to_datetime(strategy_entry_cutoff, format='%H:%M:%S')
            strategy_exit_time = strategy_obj.__dict__.get('exit_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            exit_time = pd.to_datetime(strategy_exit_time, format='%H:%M:%S')
            strategy_entry_filter_ema = strategy_obj.__dict__.get('entry_filter_ema')

            # Initialize is_entry_trigger and is_entry_filter with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_entry_filter'] = False
            self.df_hist_data['is_exit_trigger'] = False
            close_col_index = self.df_hist_data.columns.get_loc('close')
            entry_candle_low = np.nan
            is_trade_open = np.nan
            self.df_hist_data.insert(loc=close_col_index + 3, column='entry_candle_low', value=entry_candle_low)
            self.df_hist_data.insert(loc=close_col_index + 4, column='is_trade_open', value=is_trade_open)

            # Convert the Series of strings in YYYY-mm-dd HH:MM:SS format to datetime objects in HH:MM:SS format
            # Convert the datetime objects to strings in HH:MM:SS format and then convert them to datetime objects in HH:MM:SS format
            candle_open_time = pd.to_datetime(pd.to_datetime(self.df_hist_data['candle_sttime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%H:%M:%S'), format='%H:%M:%S')

            # Condition for is_entry_trigger: 3 min price closed above first 3 min candle close * multiplier in previous row
            # and current candle open time >= strategy entry_time and < strategy entry_cut_off
            condition_entry = (
                                (self.df_hist_data['gma_val'].shift(2) <= self.df_hist_data['first_3m_high_extended'].shift(2)) & \
                                (self.df_hist_data['gma_val'].shift(1) > self.df_hist_data['first_3m_high_extended'].shift(1))
                            ) & \
                            (self.df_hist_data['open'] > self.df_hist_data['low'].shift(1)) & \
                            (candle_open_time >= entry_time) & (candle_open_time < entry_cut_off)

            self.df_hist_data['entry_candle_low'] = self.df_hist_data.groupby('candle_date')['low'].shift(1).where(condition_entry)
            self.df_hist_data['entry_candle_low'] = self.df_hist_data.groupby('candle_date')['entry_candle_low'].ffill()

            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_entry_filter if it is configured to True: rma_ema_val in previous row > st_val in previous row and st_dir in previous row == 1
            # else set filter condition to entry condition 
            if strategy_entry_filter_ema:
                # condition_filter = condition_entry
                # Evaluate filter condition
                #condition_filter = ((self.df_hist_data['close'] > self.df_hist_data['rma_ema_val']) | (self.df_hist_data['close'] > self.df_hist_data['st_val'])) & \
                #                condition_entry
                condition_filter = (self.df_hist_data['close'] > self.df_hist_data['rma_ema_val']) & condition_entry
            else:
                condition_filter = condition_entry
            
            self.df_hist_data.loc[condition_filter, 'is_entry_filter'] = True
            self.df_hist_data.loc[condition_filter, 'is_trade_open'] = float(True)

            # Condition for is_exit_trigger: close in row before previous row >= entry candle low AND close in previous row < entry candle low
            """
            condition_exit = (
                                ((self.df_hist_data['close'].shift(2) >= self.df_hist_data['first_3m_high_extended'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) < self.df_hist_data['first_3m_high_extended'].shift(1))) | \
                                ((self.df_hist_data['close'].shift(2) >= self.df_hist_data['entry_candle_low'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) < self.df_hist_data['entry_candle_low'].shift(1))) | \
                                (candle_open_time >= exit_time)
                            )
            """
            
            # Condition for is_exit_trigger: close in row before previous row >= atr trailing stop loss AND close in previous row < atr trailing stop loss
            condition_exit = (
                                ((self.df_hist_data['close'].shift(2) >= self.df_hist_data['atr_tsl_long'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) < self.df_hist_data['atr_tsl_long'].shift(2))) | \
                                (candle_open_time >= exit_time)
                            )

            self.df_hist_data.loc[condition_exit, 'is_exit_trigger'] = True
            self.df_hist_data.loc[condition_exit, 'is_trade_open'] = float(False)

            self.df_hist_data['is_trade_open'] = self.df_hist_data['is_trade_open'].ffill().fillna(False)
            self.df_hist_data['is_trade_open'] = self.df_hist_data['is_trade_open'].astype(bool)

        elif strategy_id in ['NIFTY_S06']:

            strategy_entry_time = strategy_obj.__dict__.get('entry_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_time = pd.to_datetime(strategy_entry_time, format='%H:%M:%S')
            strategy_entry_cutoff = strategy_obj.__dict__.get('entry_cutoff')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_cut_off = pd.to_datetime(strategy_entry_cutoff, format='%H:%M:%S')
            strategy_exit_time = strategy_obj.__dict__.get('exit_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            exit_time = pd.to_datetime(strategy_exit_time, format='%H:%M:%S')
            strategy_entry_filter_ema = strategy_obj.__dict__.get('entry_filter_ema')

            # Initialize is_entry_trigger and is_entry_filter with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_entry_filter'] = False
            self.df_hist_data['is_exit_trigger'] = False
            close_col_index = self.df_hist_data.columns.get_loc('close')
            entry_candle_high = np.nan
            is_trade_open = np.nan
            self.df_hist_data.insert(loc=close_col_index + 3, column='entry_candle_high', value=entry_candle_high)
            self.df_hist_data.insert(loc=close_col_index + 4, column='is_trade_open', value=is_trade_open)

            # Convert the Series of strings in YYYY-mm-dd HH:MM:SS format to datetime objects in HH:MM:SS format
            # Convert the datetime objects to strings in HH:MM:SS format and then convert them to datetime objects in HH:MM:SS format
            candle_open_time = pd.to_datetime(pd.to_datetime(self.df_hist_data['candle_sttime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%H:%M:%S'), format='%H:%M:%S')

            # Condition for is_entry_trigger: price crossed below rma_ema_val in previous row
            # and current candle open time >= strategy entry_time and < strategy entry_cut_off
            condition_entry = (
                                (self.df_hist_data['gma_val'].shift(2) >= self.df_hist_data['first_3m_low_extended'].shift(2)) & \
                                (self.df_hist_data['gma_val'].shift(1) < self.df_hist_data['first_3m_low_extended'].shift(1))
                            ) & \
                            (self.df_hist_data['open'] < self.df_hist_data['high'].shift(1)) & \
                            (candle_open_time >= entry_time) & (candle_open_time < entry_cut_off)

            self.df_hist_data['entry_candle_high'] = self.df_hist_data.groupby('candle_date')['high'].shift(1).where(condition_entry)
            self.df_hist_data['entry_candle_high'] = self.df_hist_data.groupby('candle_date')['entry_candle_high'].ffill()

            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_entry_filter if it is configured to True: rma_ema_val in previous row > st_val in previous row and st_dir in previous row == 1
            # else set filter condition to entry condition 
            if strategy_entry_filter_ema:
                # condition_filter = condition_entry
                # Evaluate filter condition
                #condition_filter = ((self.df_hist_data['close'] < self.df_hist_data['rma_ema_val']) | (self.df_hist_data['close'] < self.df_hist_data['st_val'])) & \
                #                condition_entry
                condition_filter = (self.df_hist_data['close'] < self.df_hist_data['rma_ema_val']) & condition_entry
            else:
                condition_filter = condition_entry
            
            self.df_hist_data.loc[condition_filter, 'is_entry_filter'] = True
            self.df_hist_data.loc[condition_filter, 'is_trade_open'] = float(True)

            # Condition for is_exit_trigger: close in row before previous row <= entry candle high AND close in previous row > entry candle high
            """
            condition_exit = (
                                ((self.df_hist_data['close'].shift(2) <= self.df_hist_data['first_3m_low_extended'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) > self.df_hist_data['first_3m_low_extended'].shift(1))) | \
                                ((self.df_hist_data['close'].shift(2) <= self.df_hist_data['entry_candle_high'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) > self.df_hist_data['entry_candle_high'].shift(1))) | \
                                (candle_open_time >= exit_time)
                            )

            """

            # Condition for is_exit_trigger: close in row before previous row <= atr trailing stop loss AND close in previous row < atr trailing stop loss
            condition_exit = (
                                ((self.df_hist_data['close'].shift(2) <= self.df_hist_data['atr_tsl_short'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) > self.df_hist_data['atr_tsl_short'].shift(2))) | \
                                (candle_open_time >= exit_time)
                            )

            self.df_hist_data.loc[condition_exit, 'is_exit_trigger'] = True
            self.df_hist_data.loc[condition_exit, 'is_trade_open'] = float(False)

            self.df_hist_data['is_trade_open'] = self.df_hist_data['is_trade_open'].ffill().fillna(False)
            self.df_hist_data['is_trade_open'] = self.df_hist_data['is_trade_open'].astype(bool)

        elif strategy_id in ['NIFTY_S07']:

            strategy_entry_time = strategy_obj.__dict__.get('entry_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_time = pd.to_datetime(strategy_entry_time, format='%H:%M:%S')
            strategy_entry_cutoff = strategy_obj.__dict__.get('entry_cutoff')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_cut_off = pd.to_datetime(strategy_entry_cutoff, format='%H:%M:%S')
            strategy_exit_time = strategy_obj.__dict__.get('exit_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            exit_time = pd.to_datetime(strategy_exit_time, format='%H:%M:%S')
            strategy_entry_filter_ema = strategy_obj.__dict__.get('entry_filter_ema')

            # Initialize is_entry_trigger and is_entry_filter with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_entry_filter'] = False
            self.df_hist_data['is_exit_trigger'] = False
            close_col_index = self.df_hist_data.columns.get_loc('close')
            entry_candle_low = np.nan
            is_trade_open = np.nan
            self.df_hist_data.insert(loc=close_col_index + 3, column='entry_candle_low', value=entry_candle_low)
            self.df_hist_data.insert(loc=close_col_index + 4, column='is_trade_open', value=is_trade_open)

            # Convert the Series of strings in YYYY-mm-dd HH:MM:SS format to datetime objects in HH:MM:SS format
            # Convert the datetime objects to strings in HH:MM:SS format and then convert them to datetime objects in HH:MM:SS format
            candle_open_time = pd.to_datetime(pd.to_datetime(self.df_hist_data['candle_sttime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%H:%M:%S'), format='%H:%M:%S')

            # Condition for is_entry_trigger: 3 min price closed above first 3 min candle close * multiplier in previous row
            # and current candle open time >= strategy entry_time and < strategy entry_cut_off
            condition_entry = (
                                (self.df_hist_data['close'].shift(2) <= self.df_hist_data['rma_ema_val'].shift(2)) & \
                                (self.df_hist_data['close'].shift(1) > self.df_hist_data['rma_ema_val'].shift(1))
                            ) & \
                            (self.df_hist_data['close'] > self.df_hist_data['low'].shift(1)) & \
                            (candle_open_time >= entry_time) & (candle_open_time < entry_cut_off)

            self.df_hist_data['entry_candle_low'] = self.df_hist_data.groupby('candle_date')['low'].shift(1).where(condition_entry)
            self.df_hist_data['entry_candle_low'] = self.df_hist_data.groupby('candle_date')['entry_candle_low'].ffill()

            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_entry_filter if it is configured to True: current Close > filter_ema_val
            # else set filter condition to entry condition 
            if strategy_entry_filter_ema:
                # condition_filter = condition_entry
                # Evaluate filter condition
                #condition_filter = ((self.df_hist_data['close'] > self.df_hist_data['filter_ema_val']) & condition_entry
                condition_filter = (self.df_hist_data['close'] > self.df_hist_data['filter_ema_val']) & condition_entry
            else:
                condition_filter = condition_entry
            
            self.df_hist_data.loc[condition_filter, 'is_entry_filter'] = True
            self.df_hist_data.loc[condition_filter, 'is_trade_open'] = float(True)

            # Condition for is_exit_trigger: close in row before previous row >= entry candle low AND close in previous row < entry candle low
            """
            condition_exit = (
                                ((self.df_hist_data['close'].shift(2) >= self.df_hist_data['first_3m_high_extended'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) < self.df_hist_data['first_3m_high_extended'].shift(1))) | \
                                ((self.df_hist_data['close'].shift(2) >= self.df_hist_data['entry_candle_low'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) < self.df_hist_data['entry_candle_low'].shift(1))) | \
                                (candle_open_time >= exit_time)
                            )
            """
            
            # Condition for is_exit_trigger: close in row before previous row >= atr trailing stop loss AND close in previous row < atr trailing stop loss
            condition_exit = (
                                ((self.df_hist_data['close'].shift(2) >= self.df_hist_data['atr_tsl_long'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) < self.df_hist_data['atr_tsl_long'].shift(2))) | \
                                (candle_open_time >= exit_time)
                            )

            self.df_hist_data.loc[condition_exit, 'is_exit_trigger'] = True
            self.df_hist_data.loc[condition_exit, 'is_trade_open'] = float(False)

            self.df_hist_data['is_trade_open'] = self.df_hist_data['is_trade_open'].ffill().fillna(False)
            self.df_hist_data['is_trade_open'] = self.df_hist_data['is_trade_open'].astype(bool)

        elif strategy_id in ['NIFTY_S08']:

            strategy_entry_time = strategy_obj.__dict__.get('entry_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_time = pd.to_datetime(strategy_entry_time, format='%H:%M:%S')
            strategy_entry_cutoff = strategy_obj.__dict__.get('entry_cutoff')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_cut_off = pd.to_datetime(strategy_entry_cutoff, format='%H:%M:%S')
            strategy_exit_time = strategy_obj.__dict__.get('exit_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            exit_time = pd.to_datetime(strategy_exit_time, format='%H:%M:%S')
            strategy_entry_filter_ema = strategy_obj.__dict__.get('entry_filter_ema')

            # Initialize is_entry_trigger and is_entry_filter with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_entry_filter'] = False
            self.df_hist_data['is_exit_trigger'] = False
            close_col_index = self.df_hist_data.columns.get_loc('close')
            entry_candle_high = np.nan
            is_trade_open = np.nan
            self.df_hist_data.insert(loc=close_col_index + 3, column='entry_candle_high', value=entry_candle_high)
            self.df_hist_data.insert(loc=close_col_index + 4, column='is_trade_open', value=is_trade_open)

            # Convert the Series of strings in YYYY-mm-dd HH:MM:SS format to datetime objects in HH:MM:SS format
            # Convert the datetime objects to strings in HH:MM:SS format and then convert them to datetime objects in HH:MM:SS format
            candle_open_time = pd.to_datetime(pd.to_datetime(self.df_hist_data['candle_sttime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%H:%M:%S'), format='%H:%M:%S')

            # Condition for is_entry_trigger: price crossed below rma_ema_val in previous row
            # and current candle open time >= strategy entry_time and < strategy entry_cut_off
            condition_entry = (
                                (self.df_hist_data['close'].shift(2) >= self.df_hist_data['rma_ema_val'].shift(2)) & \
                                (self.df_hist_data['close'].shift(1) < self.df_hist_data['rma_ema_val'].shift(1))
                            ) & \
                            (self.df_hist_data['close'] < self.df_hist_data['high'].shift(1)) & \
                            (candle_open_time >= entry_time) & (candle_open_time < entry_cut_off)

            self.df_hist_data['entry_candle_high'] = self.df_hist_data.groupby('candle_date')['high'].shift(1).where(condition_entry)
            self.df_hist_data['entry_candle_high'] = self.df_hist_data.groupby('candle_date')['entry_candle_high'].ffill()

            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_entry_filter if it is configured to True: current Close < filter_ema_val
            # else set filter condition to entry condition 
            if strategy_entry_filter_ema:
                # condition_filter = condition_entry
                # Evaluate filter condition
                #condition_filter = ((self.df_hist_data['close'] < self.df_hist_data['filter_ema_val']) & condition_entry
                condition_filter = (self.df_hist_data['close'] < self.df_hist_data['filter_ema_val']) & condition_entry
            else:
                condition_filter = condition_entry
            
            self.df_hist_data.loc[condition_filter, 'is_entry_filter'] = True
            self.df_hist_data.loc[condition_filter, 'is_trade_open'] = float(True)

            # Condition for is_exit_trigger: close in row before previous row <= entry candle high AND close in previous row > entry candle high
            """
            condition_exit = (
                                ((self.df_hist_data['close'].shift(2) <= self.df_hist_data['first_3m_low_extended'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) > self.df_hist_data['first_3m_low_extended'].shift(1))) | \
                                ((self.df_hist_data['close'].shift(2) <= self.df_hist_data['entry_candle_high'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) > self.df_hist_data['entry_candle_high'].shift(1))) | \
                                (candle_open_time >= exit_time)
                            )

            """

            # Condition for is_exit_trigger: close in row before previous row <= atr trailing stop loss AND close in previous row < atr trailing stop loss
            condition_exit = (
                                ((self.df_hist_data['close'].shift(2) <= self.df_hist_data['atr_tsl_short'].shift(2)) & \
                                    (self.df_hist_data['close'].shift(1) > self.df_hist_data['atr_tsl_short'].shift(2))) | \
                                (candle_open_time >= exit_time)
                            )

            self.df_hist_data.loc[condition_exit, 'is_exit_trigger'] = True
            self.df_hist_data.loc[condition_exit, 'is_trade_open'] = float(False)

            self.df_hist_data['is_trade_open'] = self.df_hist_data['is_trade_open'].ffill().fillna(False)
            self.df_hist_data['is_trade_open'] = self.df_hist_data['is_trade_open'].astype(bool)

        elif strategy_id in ['NIFTY_S09']:

            strategy_entry_time = strategy_obj.__dict__.get('entry_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_time = pd.to_datetime(strategy_entry_time, format='%H:%M:%S')
            strategy_entry_cutoff = strategy_obj.__dict__.get('entry_cutoff')
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
                                (candle_open_time >= entry_time) & (candle_open_time < entry_cut_off)
            
            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_entry_filter: st_val in row before previous row > rma_ema_val in row before previous row
            condition_filter = (self.df_hist_data['st_val'].shift(2) > self.df_hist_data['rma_ema_val'].shift(2)) & condition_entry
            self.df_hist_data.loc[condition_filter, 'is_entry_filter'] = True

        elif strategy_id in ['NIFTY_S10']:

            strategy_entry_time = strategy_obj.__dict__.get('entry_time')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_time = pd.to_datetime(strategy_entry_time, format='%H:%M:%S')
            strategy_entry_cutoff = strategy_obj.__dict__.get('entry_cutoff')
            # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
            entry_cut_off = pd.to_datetime(strategy_entry_cutoff, format='%H:%M:%S')

            # Initialize is_entry_trigger and is_entry_filter with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_entry_filter'] = False

            # Convert the Series of strings in YYYY-mm-dd HH:MM:SS format to datetime objects in HH:MM:SS format
            # Convert the datetime objects to strings in HH:MM:SS format and then convert them to datetime objects in HH:MM:SS format
            candle_open_time = pd.to_datetime(pd.to_datetime(self.df_hist_data['candle_sttime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%H:%M:%S'), format='%H:%M:%S')

            # Condition for is_entry_trigger: close > rma_ema_val in row before previous row and close < rma_ema_val in previous row
            # and current candle open time >= strategy entry_time and < strategy entry_cut_off
            condition_entry = (self.df_hist_data['st_dir'].shift(1) == -1) & \
                                (self.df_hist_data['st_dir'].shift(2) == 1) & \
                                (candle_open_time >= entry_time) & (candle_open_time < entry_cut_off)
            
            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_entry_filter: st_val in row before previous row < rma_ema_val in row before previous row
            condition_filter = (self.df_hist_data['st_val'].shift(2) < self.df_hist_data['rma_ema_val'].shift(2)) & condition_entry
            self.df_hist_data.loc[condition_filter, 'is_entry_filter'] = True

        print(f"{str(datetime.now())} Finished Identifying Entry Trigger, Entry Filter and Exit Trigger Signal Rows for strategy_id {strategy_id}")
        return

    def set_trade_instr_details(self, strategy_obj):

        strategy_id = strategy_obj.strategy_id
        print(f"{str(datetime.now())} Setting trade instrument details for strategy_id {strategy_id}")
        #for key, value in strategy_obj.__dict__.items():
        #    print(f"Key: {key}, Value: {value}")

        if strategy_id == "NIFTY_S01":

            # Initialize is_entry_trigger and is_exit_trigger with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_exit_trigger'] = False

            # Condition for is_entry_trigger: st_dir in previous row is 1 AND st_dir in row before previous is -1
            condition_entry = (self.df_hist_data['st_dir'].shift(1) == 1) & (self.df_hist_data['st_dir'].shift(2) == -1)
            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_exit_trigger: st_dir in previous row is -1 AND st_dir in row before previous is 1
            condition_exit = (self.df_hist_data['st_dir'].shift(1) == -1) & (self.df_hist_data['st_dir'].shift(2) == 1)
            self.df_hist_data.loc[condition_exit, 'is_exit_trigger'] = True

        elif strategy_id == "NIFTY_S02":

            # Initialize is_entry_trigger and is_exit_trigger with False
            self.df_hist_data['is_entry_trigger'] = False
            self.df_hist_data['is_exit_trigger'] = False

            # Condition for is_entry_trigger: st_dir in previous row is -1 AND st_dir in row before previous is 1
            condition_entry = (self.df_hist_data['st_dir'].shift(1) == -1) & (self.df_hist_data['st_dir'].shift(2) == 1)
            self.df_hist_data.loc[condition_entry, 'is_entry_trigger'] = True

            # Condition for is_exit_trigger: st_dir in previous row is 1 AND st_dir in row before previous is -1
            condition_exit = (self.df_hist_data['st_dir'].shift(1) == 1) & (self.df_hist_data['st_dir'].shift(2) == -1)
            self.df_hist_data.loc[condition_exit, 'is_exit_trigger'] = True

        elif strategy_id in ['NIFTY_S03', 'NIFTY_S04', 'NIFTY_S05', 'NIFTY_S06', 'NIFTY_S07', 'NIFTY_S08', 'NIFTY_S09', 'NIFTY_S10']:

            strike_multiple = strategy_obj.__dict__.get('strike_multiple')
            buy_strike_offset = strategy_obj.__dict__.get('buy_strike_offset')
            buy_strike_right = strategy_obj.__dict__.get('buy_strike_right')

            condition_trade = self.df_hist_data['is_entry_filter']
            self.df_hist_data.loc[condition_trade, 'buy_strike'] = (self.get_buy_strike(self.df_hist_data['open'], strike_multiple, buy_strike_offset, buy_strike_right)).astype(int)
            self.df_hist_data['buy_strike'] = self.df_hist_data['buy_strike'].fillna(0).astype(int)

            df_buy_strike_expiry_details = self.get_buy_strike_expiry_details(self.df_hist_data['candle_sttime'], strategy_id)
            condition_trade = self.df_hist_data['is_entry_filter']
            self.df_hist_data.loc[condition_trade, 'buy_strike_expiry'] = df_buy_strike_expiry_details['buy_strike_expiry'].astype(str)
            self.df_hist_data.loc[condition_trade, 'buy_strike_expiry_type'] = df_buy_strike_expiry_details['buy_strike_expiry_type'].astype(str)
            self.df_hist_data.loc[condition_trade, 'buy_strike_contract_file'] = df_buy_strike_expiry_details['buy_strike_contract_file'].astype(str)
            self.df_hist_data.loc[condition_trade, 'buy_strike_right'] = buy_strike_right

            self.df_hist_data.reset_index(drop=True, inplace=True)

        print(f"{str(datetime.now())} Finished setting Trade Instrument Details for strategy_id {strategy_id}")
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
    def get_buy_strike_expiry_details(self, candle_sttime_series, strategy_id) -> pd.DataFrame:

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
                if strategy_id == "NIFTY_S01":

                    curr_contracts_file_name = self.curr_opt_contracts_nf_file_name

                elif strategy_id == "NIFTY_S02":

                    curr_contracts_file_name = self.curr_opt_contracts_nf_file_name

                elif strategy_id in ['NIFTY_S03', 'NIFTY_S04', 'NIFTY_S05', 'NIFTY_S06', 'NIFTY_S07', 'NIFTY_S08', 'NIFTY_S09', 'NIFTY_S10']:
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

    def update_buy_strike_contracts_details(self, signal_buy_strike_series, strategy_obj) -> pd.DataFrame:

        strategy_id = strategy_obj.strategy_id
        signal_file = strategy_obj.signal_file
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

        if strategy_id == "NIFTY_S01":

            curr_contracts_file_name = self.curr_opt_contracts_nf_file_name

        elif strategy_id == "NIFTY_S02":

            curr_contracts_file_name = self.curr_opt_contracts_nf_file_name

        elif strategy_id in ['NIFTY_S03', 'NIFTY_S04', 'NIFTY_S05', 'NIFTY_S06', 'NIFTY_S07', 'NIFTY_S08', 'NIFTY_S09', 'NIFTY_S10']:

            df_signal_file = pd.read_csv(signal_file, usecols=['buy_strike', 'buy_strike_expiry', 'buy_strike_right', 'buy_strike_contract_file'], dtype={'buy_strike': int, 'buy_strike_expiry': str, 'buy_strike_right': str, 'buy_strike_contract_file': str})
            df_signal_file_trade = df_signal_file.iloc[trade_indices]

            for i, row in df_signal_file_trade.iterrows():
                buy_strike = row['buy_strike']
                buy_strike_expiry = row['buy_strike_expiry']
                buy_strike_right = row['buy_strike_right']

                df_contract_file = pd.read_csv(row['buy_strike_contract_file'], usecols=['expiry', 'instrument_key', 'instrument_type', 'lot_size', 'freeze_quantity', 'strike_price', 'trading_symbol'], dtype={'expiry': str, 'instrument_key': str, 'instrument_type': str, 'lot_size': int, 'freeze_quantity': int, 'strike_price': int, 'trading_symbol': str})

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

        print(f"{str(datetime.now())} Finished updating Contract Details for strategy_id {strategy_id}")
        return df_buy_strike_contract_details
