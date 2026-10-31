import os
from io import StringIO
from zipfile import ZipFile
from datetime import datetime
#from natsort import natsort_keygen
import logging, math, time, uuid
import pandas as pd
import numpy as np
from backtest_common import __backtestconfig__
from backtest_common.TALibrary_cls import TALibrary
import upstox_client
from upstox_core.data_creators.HistoryDataAPIs_cls import HistoryDataAPIs

# Create and configure logger
trade_data_creator_logger = logging.getLogger("logs/trade_data_creator.log")
trade_data_creator_logger.addHandler(logging.FileHandler("logs/trade_data_creator.log", mode='a'))
trade_data_creator_logger.setLevel(logging.INFO)

class TradeDataCreator:

    def __init__(self, broker, logger=trade_data_creator_logger): 
        self.logger=logger
        self.broker=broker
        self.history_data_raw_file_dir = __backtestconfig__.HISTORY_DATA_RAW_FILE_DIR
        self.trade_data_details_dir = __backtestconfig__.TRADE_DATA_DETAILS_DIR
        self.trade_data_handler_v3=HistoryDataAPIs()
        self.talib = TALibrary(self.broker)
        self.configuration = upstox_client.Configuration()
        self.configuration.access_token = os.environ.get("UPSTOX_ACCESS_TOKEN", "")

    def generate_unique_id(self):
        """
        Generates a unique ID by combining a UUID and a timestamp.
        """
        timestamp = int(time.time() * 1000)  # Current time in milliseconds
        unique_part = uuid.uuid4().hex       # A random UUID converted to a hex string
        return f"{timestamp}-{unique_part}"

    def create_trade_data_for_strategy(self, strategy_obj):
        strategy_id = strategy_obj.strategy_id
        signal_file = strategy_obj.signal_file
        signal_trade_file = strategy_obj.signal_trade_file
        signal_trade_details_zipfile = strategy_obj.signal_trade_details_zipfile

        list_of_trades_for_strategy = []
        
        if strategy_id in ['NIFTY_S01', 'NIFTY_S03', 'NIFTY_S05', 'BANKNIFTY_S05']:

            if not os.path.isfile(signal_file):
                print(f"{str(datetime.now())} Signal File {strategy_obj.signal_file} for Strategy {strategy_obj.strategy_id} not found")
                self.logger.exception(f"Trade Data Creator loading exception: File not found {signal_file}")
                raise FileNotFoundError(f"Trade Data Creator loading error: File not found {signal_file}")

            self.df_signal_data = pd.read_csv(signal_file, \
                                              dtype={'candle_sttime': str, 'open': float, 'high': float, 'low': float, 'close': float, \
                                                     'first_candle_high': float, 'first_candle_high_extended': float, \
                                                        'vol': float, 'ema_val': float, 'rma_ema_val': float, 'atr_tsl_long': float, \
                                                            'is_entry_trigger': bool, 'is_entry_filter': bool, \
                                                                'buy_strike': float, 'buy_strike_expiry': str, 'buy_strike_expiry_type': str, 'buy_strike_right': str, \
                                                                    'instrument_key': str, 'trading_symbol': str, 'lot_size': int, 'freeze_quantity': int})
            
            if self.df_signal_data.empty:
                self.logger.exception(f"Trade Data Creator loading exception: Signal File is empty {signal_file}")
                raise ValueError(f"Trade Data Creator loading error: Signal File is empty {signal_file}")
            
            list_of_trades_for_strategy = self.create_list_of_trades_for_strategy(self.df_signal_data, strategy_obj)
            #print(f"{str(datetime.now())} Created list of trades for Strategy {strategy_id} - {list_of_trades_for_strategy}")

        elif strategy_id in ['NIFTY_S02', 'NIFTY_S04', 'NIFTY_S06', 'BANKNIFTY_S06']:

            if not os.path.isfile(signal_file):
                print(f"{str(datetime.now())} Signal File {strategy_obj.signal_file} for Strategy {strategy_obj.strategy_id} not found")
                self.logger.exception(f"Trade Data Creator loading exception: File not found {signal_file}")
                raise FileNotFoundError(f"Trade Data Creator loading error: File not found {signal_file}")

            self.df_signal_data = pd.read_csv(signal_file, \
                                              dtype={'candle_sttime': str, 'open': float, 'high': float, 'low': float, 'close': float, \
                                                     'first_candle_low': float, 'first_candle_low_extended': float, \
                                                        'vol': float, 'ema_val': float, 'rma_ema_val': float, 'atr_tsl_short': float, \
                                                            'is_entry_trigger': bool, 'is_entry_filter': bool, \
                                                                'buy_strike': float, 'buy_strike_expiry': str, 'buy_strike_expiry_type': str, 'buy_strike_right': str, \
                                                                    'instrument_key': str, 'trading_symbol': str, 'lot_size': int, 'freeze_quantity': int})
            
            if self.df_signal_data.empty:
                self.logger.exception(f"Trade Data Creator loading exception: Signal File is empty {signal_file}")
                raise ValueError(f"Trade Data Creator loading error: Signal File is empty {signal_file}")

            list_of_trades_for_strategy = self.create_list_of_trades_for_strategy(self.df_signal_data, strategy_obj)
            #print(f"{str(datetime.now())} Created list of trades for Strategy {strategy_id} - {list_of_trades_for_strategy}")

        signal_trade_df = pd.DataFrame(list_of_trades_for_strategy, columns=['trade_date', 'buy_datetime', 'sell_datetime', 'investment_amount', 'instrument_key', 'trading_symbol', \
                                                                              'lot_size', 'num_of_lots', 'overall_pnl', 'pnl_realized', 'slippage', 'net_pnl_after_slippage','profit_left_on_the_table','max_unrealized_profit_during_trade', 'max_unrealized_loss_during_trade', 'trade_duration', 'exit_reason'])
        
        trade_id_list = []
        trade_details_list = []
        trade_details_df = pd.DataFrame(list_of_trades_for_strategy, columns=['strategy_id', 'trade_instr_data'])

        strategy_obj.signal_trade_details = {}
        strategy_obj.signal_trade_details_files = {}

        trade_id = 0

        #Code to write Trade details files inside TradeDetails folder
        for index, row in trade_details_df.iterrows():
            trade_details = row['trade_instr_data']
            trade_id = index+1
            trade_id_list.append(trade_id)
            trade_details.insert(0, 'trade_id', trade_id)
            trade_details_list.append(trade_details)
            trade_details_file_name = f"{strategy_id}_Trade_Details_File_{trade_id}.csv"
            trade_details_file = os.path.join(self.trade_data_details_dir, trade_details_file_name)

            with open(trade_details_file, "wt", newline='') as cfile:
                cfile.write(f"{trade_details.to_csv(index=False, header=True)}")
            # print(f"{str(datetime.now())} Finished writing Trade Details File {trade_details_file} for strategy_id {strategy_id}")
            strategy_obj.signal_trade_details[trade_id] = trade_details
            strategy_obj.signal_trade_details_files[trade_id] = trade_details_file
        
        signal_trade_df.insert(0, column='trade_id', value=trade_id_list)

        print(f"{str(datetime.now())} Finished writing Trade Details Files for each trade in {signal_trade_file} for strategy_id {strategy_id}")

        strategy_obj.signal_trades = signal_trade_df
        with open(signal_trade_file, "wt", newline='') as cfile:
            cfile.write(f"{signal_trade_df.to_csv(index=False, header=True)}")
        print(f"{str(datetime.now())} Finished writing Signal Trade File {signal_trade_file} for strategy_id {strategy_id}")

        final_trade_details_file = os.path.join(__backtestconfig__.FINAL_TRADE_DETAILS_DIR, f"{strategy_id}_Final_Trade_Details_File.csv")
        merged_trade_details_df = pd.concat(trade_details_list, ignore_index=True)

        final_trade_details_df = pd.merge(signal_trade_df, merged_trade_details_df, on=['trade_id', 'buy_datetime'], how='outer')
        final_trade_details_df.sort_values(by=['trade_id', 'buy_datetime'], ascending=[True, True], inplace=True)
        final_trade_details_df.reset_index(drop=True, inplace=True)

        with open(final_trade_details_file, "wt", newline='') as cfile:
            cfile.write(f"{final_trade_details_df.to_csv(index=False, header=True)}")
        print(f"{str(datetime.now())} Finished writing Final Trade Details File {final_trade_details_file} for strategy_id {strategy_id}")

        return

    def create_list_of_trades_for_strategy(self, df_signal_data, strategy_obj) -> list:
        strategy_id = strategy_obj.strategy_id
       
        print(f"{str(datetime.now())} Creating trade list for Strategy {strategy_id}")

        # Get configurable values from Strategy Object
        entry_cutoff_time = strategy_obj.__dict__.get('entry_cutoff')
        if isinstance(entry_cutoff_time, str):
            # Convert string to datetime.time object
            entry_cutoff_time = datetime.strptime(entry_cutoff_time, '%H:%M:%S').time()
        elif isinstance(entry_cutoff_time, datetime):
            # If it's already a datetime object, extract the time
            entry_cutoff_time = entry_cutoff_time.time()
        nse_symbol = strategy_obj.__dict__.get('nse_symbol')
        trade_feed_interval = strategy_obj.__dict__.get('trade_feed_interval')
        feed_interval_unit = strategy_obj.__dict__.get('feed_interval_unit')
        trade_feed_interval_exp = strategy_obj.__dict__.get('trade_feed_interval_exp')
        stage_2_trigger_pct = strategy_obj.__dict__.get('stage_2_trigger_pct') #0.20
        trailing_stop_pct = strategy_obj.__dict__.get('trailing_stop_pct') #0.15
        exit_atr_length = strategy_obj.__dict__.get('exit_atr_length')
        exit_atr_multiplier = strategy_obj.__dict__.get('exit_atr_multiplier')
        exit_threshold = strategy_obj.__dict__.get('exit_threshold')
        profit_threshold = strategy_obj.__dict__.get('profit_threshold')
        strategy_exit_time = strategy_obj.__dict__.get('exit_time')
        # Convert the string in HH:MM:SS format to datetime object in HH:MM:SS format
        exit_time = pd.to_datetime(strategy_exit_time, format='%H:%M:%S')
        trade_direction = strategy_obj.__dict__.get('trade_direction')
        day_loss_limit = strategy_obj.__dict__.get('day_loss_limit')

        if nse_symbol == "NSE_INDEX|Nifty 50" and feed_interval_unit == "minutes":
            history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, f"Nifty_HistoryData_{trade_feed_interval}m.csv")
        elif nse_symbol == "NSE_INDEX|Nifty 50" and feed_interval_unit == "days":
            history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, f"Nifty_HistoryData_daily.csv")
        elif nse_symbol == "NSE_INDEX|Nifty 50" and feed_interval_unit == "weeks":
            history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, f"Nifty_HistoryData_weekly.csv")
        elif nse_symbol == "NSE_INDEX|Nifty Bank" and feed_interval_unit == "minutes":
            history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, f"BankNifty_HistoryData_{trade_feed_interval}m.csv")
        elif nse_symbol == "NSE_INDEX|Nifty Bank" and feed_interval_unit == "days":
            history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, f"BankNifty_HistoryData_daily.csv")
        elif nse_symbol == "NSE_INDEX|Nifty Bank" and feed_interval_unit == "weeks":
            history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, f"BankNifty_HistoryData_weekly.csv")

        # Load 1-min Index data once (Assuming path is configured)
        index_1min_df = pd.read_csv(history_data_raw_file, parse_dates=['candle_sttime']).sort_values('candle_sttime')
        index_1min_df['candle_sttime'] = pd.to_datetime(index_1min_df['candle_sttime']).dt.tz_localize(None)
        index_1min_df = index_1min_df.sort_values('candle_sttime')

        # Create a list to hold trade data
        trade_list = []
        
        # Create a dictionary to hold data for each signal and corresponding trade data
        signal_trade_data = {}

        # Create a dictionary to hold date wise pnl_realized
        date_wise_realized_pnl = {}

        # Create a dictionary to hold date wise active trade
        date_wise_active_trade = {}

        # Ensure 'candle_sttime' is a datetime object
        df_signal_data['candle_sttime'] = pd.to_datetime(df_signal_data['candle_sttime'])

        overall_pnl = 0.0

        previous_row = None

        # Iterate through the Signal DataFrame to fetch corresponding Trade data
        for i, row in df_signal_data.iterrows():
            trade_date = row['candle_date']
            trade_dttime = pd.to_datetime(row['candle_sttime']).tz_localize(None)
            if previous_row is not None:
                from_date = previous_row['candle_date']
            else:
                from_date = trade_date
            to_date = trade_date
            previous_row = row
            
            print(f"Processing trade on {trade_dttime}")

            """
            # Check for daily loss limit breach
            if trade_date not in date_wise_realized_pnl:
                # print(f"No Realized PnL found for trade on {trade_date}. Initializing to 0.0.")
                date_wise_realized_pnl[trade_date] = 0.0
            
            if date_wise_realized_pnl[trade_date] < -day_loss_limit:
                print(f"Skipping trade on {trade_dttime} with Realized PnL: {date_wise_realized_pnl[trade_date]} as it exceeds daily loss limit of {day_loss_limit}.")
                continue # Skip the current trade and move to the next iteration of the loop
            """
            
            # Check for existing active trade on the same day
            if trade_date not in date_wise_active_trade:
                # print(f"No Trade Exit Time found for trade taken at {trade_dttime}. Setting active trade time.")
                date_wise_active_trade[trade_date] = pd.to_datetime(trade_dttime, format='%Y-%m-%d %H:%M:%S')
            else:
                if pd.to_datetime(trade_dttime, format='%Y-%m-%d %H:%M:%S') >= date_wise_active_trade[trade_date]:
                    date_wise_active_trade[trade_date] = pd.to_datetime(trade_dttime, format='%Y-%m-%d %H:%M:%S')
                else:
                    print(f"Skipping trade on {trade_dttime} as an active trade already exists with exit at {date_wise_active_trade[trade_date]}.")
                    continue # Skip the current trade and move to the next iteration of the loop
                
            instr_key = row['instrument_key']
            trading_symbol = row['trading_symbol']
            print(f"Fetching trade data for {instr_key} for {trading_symbol} for trade on {trade_dttime}")
            investment_amount = row['investment_amount'] if 'investment_amount' in row else strategy_obj.__dict__.get('investment_amount')
            lot_size = row['lot_size'] if 'lot_size' in row else strategy_obj.__dict__.get('lot_size')
            expiry_type = row['buy_strike_expiry_type']

            # If expiry_type is "current", Upstox API call requires interval and unit to be passed as two separate parameters "3" and "minutes"
            # If expiry_type is "expired", Upstox API call requires interval and unit to be passed together as "3minute"; note the string "minute" instead of "minutes"
            if (expiry_type == "current"):
                trade_instr_data = self.trade_data_handler_v3.get_historical_candle_data1(
                    self.configuration, instr_key, feed_interval_unit, trade_feed_interval, to_date, from_date)
            elif (expiry_type == "expired"):                
                trade_instr_data = self.trade_data_handler_v3.get_expired_historical_data(
                    self.configuration, instr_key, trade_feed_interval_exp, to_date, from_date)

            # Initialize trade metrics
            pnl_realized = 0.0
            max_profit_potential = 0.0
            max_loss_potential = 0.0

            if len(trade_instr_data.data.candles) > 0:
                trade_instr_data.data.candles.reverse()
                my_columns = {'candle_sttime': str, 'open': float, 'high': float, 'low': float, 'close': float, 'vol': float, 'oi': float}
                df = pd.DataFrame(data=np.array(trade_instr_data.data.candles), columns=my_columns.keys()).astype(my_columns)
                df.drop('vol', axis=1, inplace=True)
                df.drop('oi', axis=1, inplace=True)

                candle_sttime_col_index = df.columns.get_loc('candle_sttime')
                df['candle_sttime'] = pd.to_datetime(df['candle_sttime']).dt.tz_localize(None)
                #df.loc[:, 'candle_sttime'] = pd.to_datetime(df['candle_sttime'], format='%Y-%m-%dT%H:%M:%S%z').dt.strftime('%Y-%m-%d %H:%M:%S')
                candle_date = pd.to_datetime(df['candle_sttime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%Y-%m-%d')
                df.insert(loc=candle_sttime_col_index + 1, column='candle_date', value=candle_date)

                # Check if trade candle is on or after trade signal candle
                condition = pd.to_datetime(df['candle_sttime'], format='%Y-%m-%d %H:%M:%S') >= pd.to_datetime(trade_dttime, format='%Y-%m-%d %H:%M:%S')
                df_previous_rows = df[~condition]
                df = pd.concat([df_previous_rows.tail(1), df[condition]])
                df.reset_index(drop=True, inplace=True)

                df.drop(index=df.index[0], inplace=True)
                df.reset_index(drop=True, inplace=True)

                df['candle_sttime'] = pd.to_datetime(df['candle_sttime'], format='%Y-%m-%dT%H:%M:%S%z').dt.tz_localize(None)

                # Merge Option Data with same interval Index Spot Data
                # This is to get Index Spot prices for Stop Loss calculations in Stage 1 of trade
                df_merged = pd.merge_asof(
                    df.sort_values('candle_sttime'),
                    index_1min_df[['candle_sttime', 'open', 'high', 'low', 'close']].sort_values('candle_sttime'),
                    on='candle_sttime',
                    direction='backward',
                    suffixes=('_opt', '_idx')
                )
                if df_merged.empty:
                    print(f"No merged trade data found for trade on {trade_dttime}. Skipping this trade.")
                    continue
                
                # Get the value of open price from the first row
                #buy_price = df_merged['open_opt'].iloc[0] if not pd.isna(df_merged['open_opt'].iloc[0]) else 0.0
                # Add 1 to the buy_price to account for at_market price slippage
                buy_price = df_merged['open_opt'].iloc[0]+1
                # Add column with all values equal to the buy_price
                df_merged['buy_price'] = buy_price
                buy_datetime = df_merged['candle_sttime'].iloc[0]
                df_merged['buy_datetime'] = buy_datetime
                # Calculate number of lots to trade
                num_of_lots = self.calculate_lots_to_trade(investment_amount, buy_price, lot_size)

                # First row is the entry candle, so Lock Index Stop as it low or high for Long or Short trade respectively 
                # fixed_index_stop = df_merged['low_idx'].iloc[0] if trade_direction == "LONG" else df_merged['high_idx'].iloc[0]

                # Strategy Loop Variables
                pnl_realized = 0.0
                max_profit_potential = 0.0
                max_loss_potential = 0.0
                stage_1_no_loss_active = False
                no_loss_trailing_stop = 0.0
                stage_2_active = False
                stage_2_peak = 0.0
                
                # Initialize columns to be included in Trade Details CSV
                df_merged['trading_symbol'] = ""
                df_merged['lot_size'] = 0.0
                df_merged['num_of_lots'] = 0.0
                df_merged['is_trade_open'] = True
                df_merged['buy_datetime'] = buy_datetime
                df_merged['sell_datetime'] = None
                df_merged['trade_duration'] = 0.0
                df_merged['buy_price'] = buy_price
                df_merged['sell_price'] = None
                df_merged['pnl_unrealized'] = 0.0
                df_merged['max_profit_unrealized'] = 0.0
                df_merged['max_loss_unrealized'] = 0.0
                df_merged['pnl_realized'] = 0.0
                df_merged['exit_reason'] = ""

                df_merged.loc[0, 'is_trade_open'] = True

                for j in range(1, len(df_merged)):
                    # Get previous and current row
                    prev_row = df_merged.iloc[j-1]
                    curr_row = df_merged.iloc[j]
                    trade_duration = round((curr_row['candle_sttime'] - buy_datetime).total_seconds() / 60.0, 0)

                    # Update Unrealized Stats for Logging
                    prev_pnl = (prev_row['close_opt'] - buy_price) * row['lot_size'] * num_of_lots #if trade_direction == "LONG" else (buy_price - prev_row['close_opt']) * row['lot_size'] * num_of_lots
                    
                    # Activate Stage 1 once trade has achieved +5k profit
                    if not stage_1_no_loss_active and not stage_2_active and prev_pnl >= 5000:
                        stage_1_no_loss_active = True
                    
                    # Update Max Unrealized Profit/Loss Potential based on High/Low of previous candle                    
                    profit_instant = (prev_row['high_opt'] - buy_price) * row['lot_size'] * num_of_lots #if trade_direction == "LONG" else (buy_price - prev_row['low_opt']) * row['lot_size'] * num_of_lots
                    loss_instant = (prev_row['low_opt'] - buy_price) * row['lot_size'] * num_of_lots #if trade_direction == "LONG" else (buy_price - prev_row['high_opt']) * row['lot_size'] * num_of_lots
                    # Accumulate max profit potential (Max Favourable Excursion - MFE) and max loss potential (Max Adverse Excursion - MAE) over the trade duration to get a sense of how much unrealized profit was left on the table at the time of exit and how much unrealized loss was avoided by exiting when we did
                    max_profit_potential = max(max_profit_potential, profit_instant)
                    max_loss_potential = min(max_loss_potential, loss_instant)

                    df_merged.at[j-1, 'trade_duration'] = trade_duration
                    df_merged.at[j-1, 'pnl_unrealized'] = round(prev_pnl, 2)
                    df_merged.at[j-1, 'max_profit_unrealized'] = round(max_profit_potential, 2)
                    df_merged.at[j-1, 'max_loss_unrealized'] = round(max_loss_potential, 2)
                    df_merged.at[j-1, 'is_trade_open'] = True
                    
                    is_exit = False
                    sell_price = curr_row['open_opt'] - 1 # Default slippage exit
                    reason = ""

                    # 1. Stage 2 Activation
                    # if not stage_2_active:
                    #     prem_profit_pct = (prev_row['close_opt'] - buy_price)/buy_price #if trade_direction == "LONG" else (prev_row['low_opt'] - buy_price)/buy_price
                    #     if prem_profit_pct >= stage_2_trigger_pct:
                    #         stage_2_active = True
                    if not stage_2_active and max_profit_potential >= 15000:
                        # Only activate Stage 2 if profit potential has reached a certain threshold to avoid activating trailing stop loss too early
                        # when the profit potential is still low and can be easily eroded by normal price fluctuations
                        stage_2_peak = max_profit_potential
                        stage_2_active = True
                        # Disable Stage 1 once Stage 2 takes over as the exit decisions will now be based on the max profit trail stop in Stage 2 instead of the no loss trailing stop in Stage 1
                        stage_1_no_loss_active = False

                    # 2. Condition Checks
                    if curr_row['candle_sttime'].time() >= exit_time.time():
                        is_exit, reason = True, f"Closed Position at {exit_time.time()} as per strategy time exit rules"
                    elif prev_pnl < -exit_threshold:
                        is_exit, reason = True, f"Hard SL Loss more than {exit_threshold}"
                    elif max_loss_potential <= -7000:
                        is_exit, reason = True, f"Max Unrealized Loss more than -7000, No reason to hold further"
                    elif trade_duration > 15 and max_profit_potential < 1000:
                        is_exit, reason = True, f"No Follow-through. Max Profit not crossed 1000 even after 15 mins"
                    elif trade_duration > 20 and max_profit_potential < 2000:
                        is_exit, reason = True, f"No Follow-through. Max Profit not crossed 2000 even after 20 mins"
                    elif trade_duration > 30 and max_profit_potential < 5000:
                        is_exit, reason = True, f"No Follow-through. Max Profit not crossed 5000 even after 30 mins"
                    elif trade_duration > 45 and max_profit_potential < 6000:
                        is_exit, reason = True, f"No Follow-through. Max Profit not crossed 6000 even after 45 mins"
                    # elif not stage_1_no_loss_active and not stage_2_active:
                    #     # Stage 1: Fixed Index Stop Loss
                    #     if strategy_id in ['NIFTY_S01', 'NIFTY_S03', 'NIFTY_S05', 'BANKNIFTY_S05']:
                    #         fixed_index_stop = row['entry_candle_low']
                    #     elif strategy_id in ['NIFTY_S02', 'NIFTY_S04', 'NIFTY_S06', 'BANKNIFTY_S06']:
                    #         fixed_index_stop = row['entry_candle_high']
                    #     else:
                    #         fixed_index_stop = row['entry_candle_low'] if trade_direction == "LONG" else row['entry_candle_high']
                    #     if (trade_direction == "LONG" and prev_row['close_idx'] < fixed_index_stop):
                    #         is_exit, reason = True, f"Spot Entry Candle Low {fixed_index_stop} breached"
                    #     elif (trade_direction == "SHORT" and prev_row['close_idx'] > fixed_index_stop):
                    #         is_exit, reason = True, f"Spot Entry Candle High {fixed_index_stop} breached"
                    # Stage 2: Trail 33% from the peak profit potential
                    elif stage_2_active:
                        stage_2_peak = max(stage_2_peak, max_profit_potential)
                        # Calculate Stop PnL
                        # Example: Peak is 10k, trail pullback allowed is 33%, Stop PnL is 6.7k.
                        max_profit_trail_stop = stage_2_peak * (1 - trailing_stop_pct)
                        # Exit if unrealized pnL goes below trail level PnL
                        if prev_pnl < max_profit_trail_stop:
                            is_exit = True
                            # Realistic Exit at next candle (index j+1) open price minus slippage
                            # Handle the edge case where the exit happens on the very last candle of the data
                            if j + 1 < len(df_merged):
                                sell_price = df_merged['open_opt'].iloc[j+1] - 1 # Next Open + Slippage
                            else:
                                sell_price = curr_row['close_opt'] - 1 # Last candle Close + Slippage
                            reason = f"S2 Unrealized PnL goes below trail stop of {max_profit_trail_stop:0.2f} or ({(1 - trailing_stop_pct)*100:0.2f}% of peak {stage_2_peak:0.2f}) profit potential"
                    elif stage_1_no_loss_active:
                        if prev_pnl < 0:
                            is_exit, reason = True, "Profit Booked after No Loss Trailing Threshold breached"
                    """
                    elif not stage_2_active:
                        # Stage 1: Fixed Index Stop Loss
                        if strategy_id in ['NIFTY_S03', 'NIFTY_S05', 'BANKNIFTY_S05']:
                            fixed_index_stop = row['first_candle_high']
                        elif strategy_id in ['NIFTY_S04', 'NIFTY_S06', 'BANKNIFTY_S06']:
                            fixed_index_stop = row['first_candle_low']
                        else:
                            fixed_index_stop = row['entry_candle_low'] if trade_direction == "LONG" else row['entry_candle_high']
                        if (trade_direction == "LONG" and prev_row['close_idx'] < fixed_index_stop) or \
                        (trade_direction == "SHORT" and prev_row['close_idx'] > fixed_index_stop):
                            is_exit, reason = True, "S1 Index Stop"
                    # Stage 2: 15% Premium Trailing Stop with a FLOOR of minimum +20% PnL to be locked from Stage 1---
                    elif stage_2_active:
                        # Update Peak Unrealized Profit (max_profit_potential tracks PnL amount)
                        peak_unreal_pnl = (prev_row['high_opt'] - buy_price) * row['lot_size'] * num_of_lots
                        max_profit_potential = max(max_profit_potential, peak_unreal_pnl)
                        # Calculate Stop PnL: Trail 20% from the peak
                        # Example: Peak is 10k, trail is 2k, Stop PnL is 8k.
                        trail_pnl_stop = max_profit_potential * (1 - trailing_stop_pct)
                        
                        # Define the FLOOR: The exact price point that represents +20% profit
                        # This is to ensure Stop PnL never drops below Stage 1 profit (20% of entry)
                        stage_1_pnl_floor = (buy_price * stage_2_trigger_pct) * row['lot_size'] * num_of_lots
                        actual_pnl_stop_level = max(trail_pnl_stop, stage_1_pnl_floor)

                        # 4. Trigger Check: Did current minute's PnL go below the stop level?
                        curr_unreal_pnl = (prev_row['close_opt'] - buy_price) * row['lot_size'] * num_of_lots
                        
                        # Exit if unrealized pnL goes below trail level PnL but ensure exit price is at least the floor
                        if curr_unreal_pnl <= actual_pnl_stop_level:
                            is_exit = True
                            # Realistic Exit at next candle (index j+1) open price minus slippage
                            # Handle the edge case where the exit happens on the very last candle of the data
                            if j + 1 < len(df_merged):
                                sell_price = df_merged['open_opt'].iloc[j+1] - 1 # Next Open + Slippage
                            else:
                                sell_price = curr_row['close_opt'] - 1 # Last candle Close + Slippage
                            reason = f"S2 Trail ensuring minimum ({stage_2_trigger_pct}% profit from Stage 1 is locked if unrealized pnL goes below trail level)"
                    """
                    """
                    # Trailing 15% of price movement from max_profit_potential
                    elif stage_2_active:
                        if trade_direction == "LONG":
                            max_profit_potential = max(max_profit_potential, prev_row['high_opt'])
                            if prev_row['low_opt'] <= (max_profit_potential * (1 - trailing_stop_pct)):
                                is_exit, sell_price, reason = True, max_profit_potential * (1 - trailing_stop_pct), "S2 Trail"
                        elif trade_direction == "SHORT":
                            max_profit_potential = min(max_profit_potential, prev_row['low_opt'])
                            if prev_row['high_opt'] >= (max_profit_potential * (1 + trailing_stop_pct)):
                                is_exit, sell_price, reason = True, max_profit_potential * (1 + trailing_stop_pct), "S2 Trail"
                    """

                    if is_exit:
                        df_merged.at[j, 'trading_symbol'] = row['trading_symbol']
                        df_merged.at[j, 'lot_size'] = row['lot_size']
                        df_merged.at[j, 'num_of_lots'] = num_of_lots
                        df_merged.at[j, 'is_trade_open'] = False
                        sell_datetime = pd.to_datetime(curr_row['candle_sttime'], format='%Y-%m-%d %H:%M:%S')
                        date_wise_active_trade[trade_date] = sell_datetime
                        df_merged.at[j, 'sell_datetime'] = sell_datetime
                        df_merged.at[j, 'sell_price'] = round(sell_price, 2)
                        df_merged.at[j, 'trade_duration'] = trade_duration
                        df_merged.at[j, 'max_profit_unrealized'] = round(max_profit_potential, 2)
                        df_merged.at[j, 'max_loss_unrealized'] = round(max_loss_potential, 2)
                        pnl_realized = round((sell_price - buy_price) * row['lot_size'] * num_of_lots) #if trade_direction == "LONG" else (buy_price - sell_price) * row['lot_size'] * num_of_lots, 2)
                        df_merged.at[j, 'pnl_realized'] = pnl_realized
                        df_merged.at[j, 'exit_reason'] = reason
                        df_merged = df_merged.iloc[:j+1].copy()
                        break
                
                # Calculate final metrics for signal_trade_data
                overall_pnl += pnl_realized
                total_buy_val = buy_price * row['lot_size'] * num_of_lots
                total_sell_val = sell_price * row['lot_size'] * num_of_lots
                slippage = self.calculate_slippage(total_buy_val, total_sell_val)
                overall_pnl -= slippage

                # date_wise_realized_pnl[trade_date] += pnl_realized

                # Save Trade Data corresponding to the Signal
                signal_trade_data = {
                    'trade_date': trade_date, 
                    'instrument_key': row['instrument_key'], 
                    'trading_symbol': row['trading_symbol'], 
                    'lot_size': row['lot_size'],
                    'num_of_lots': num_of_lots, 
                    'buy_datetime': buy_datetime, 
                    'sell_datetime': sell_datetime, 
                    'buy_rate': buy_price, 
                    'sell_rate': sell_price, 
                    'overall_pnl': round(overall_pnl, 2), 
                    'pnl_realized': pnl_realized, 
                    'slippage': slippage,
                    'net_pnl_after_slippage': round(pnl_realized - slippage, 2),
                    'trade_duration': trade_duration,
                    'max_unrealized_profit_during_trade': round(max_profit_potential, 2), 
                    'profit_left_on_the_table': round(max_profit_potential - pnl_realized, 2) if pnl_realized > 0 and pnl_realized < max_profit_potential else 0,
                    'max_unrealized_loss_during_trade': round(max_loss_potential, 2), 
                    'exit_reason': reason, 
                    'strategy_id': strategy_id, 
                    'investment_amount': row.get('investment_amount', strategy_obj.investment_amount), 
                    'trade_instr_data': df_merged
                }
                # Append the DataFrame to the list
                trade_list.append(signal_trade_data)
            else:
                print(f"{str(datetime.now())} No trade instrument data found for {instr_key} from {from_date} to {to_date}")
                trade_data_creator_logger.debug(f"{str(datetime.now())} No trade instrument data found for {instr_key} from {from_date} to {to_date}")

        return trade_list
    
    # Position Sizing based on fund allocation and risk management
    def calculate_lots_to_trade(self, investment_amount, price_per_unit, lot_size):
        """
        Calculates the number of lots to be traded using math.ceil.

        Args:
            investment_amount (float): The total capital available for investment.
            price_per_unit (float): The price of a single unit of the asset.
            lot_size (int): The number of units in one lot.

        Returns:
            int: The number of lots to be traded, rounded up to the nearest whole lot.
        """
        if price_per_unit <= 0 or lot_size <= 0:
            raise ValueError("Price per unit and lot size must be positive values.")
        
        cost_per_lot = price_per_unit * lot_size
        
        # Calculate the potential number of lots, including fractions
        potential_lots = investment_amount / cost_per_lot
        
        # Round up to the nearest whole lot using math.ceil
        num_lots = math.ceil(potential_lots)
        
        return int(num_lots) # Convert to integer as lot count should be whole

    # Position Sizing based on fund allocation and risk management
    def calculate_slippage(self, total_buy_value, total_sell_value) -> float:
        """
        Calculates the slippage for a trade.

        Args:
            total_buy_value (float): The total value of the buy order.
            total_sell_value (float): The total value of the sell order.

        Returns:
            float: The slippage incurred during the trade.
        """

        STT_rate = 0.000625         # on sell side only
        txn_chg_rate = 0.0005       # both sides on premium
        SEBI_chg_rate = 0.000001    # both sides
        stamp_duty_rate = 0.00003   # on buy side only
        GST_rate = 0.18             # on SEBI + txn charges

        if self.broker in ["UPSTOX", "ICICIDIRECT"]:
            brokerage = 40.0
        else:
            brokerage = 10.0
        stt = STT_rate * total_sell_value
        transaction_charges = txn_chg_rate * (total_buy_value + total_sell_value)
        SEBI_charges = SEBI_chg_rate * (total_buy_value + total_sell_value)
        stamp_duty = stamp_duty_rate * total_buy_value
        gst = GST_rate * (transaction_charges + SEBI_charges + brokerage)

        # Calculate slippage as the difference between expected and actual revenue
        slippage = brokerage + transaction_charges + SEBI_charges + gst + stt + stamp_duty

        return slippage

        """
        Code to write Trade details files to a zip file instead of writing them to TradeDetails folder
        # Create a ZipFile object in write mode
        with ZipFile(signal_trade_details_zipfile, 'w') as zf:
            for index, row in trade_details_df.iterrows():
                trade_details = row['trade_instr_data']
                trade_id = f"{strategy_id}_{index+1}"
                trade_id_list.append(trade_id)
                trade_details_file_name = f"{trade_id}_Trade_Details_File.csv"

                # Create an in-memory text buffer
                csv_buffer = StringIO()
                # Write the DataFrame to the in-memory buffer as CSV
                trade_details.to_csv(csv_buffer, index=False)  # index=False to avoid writing DataFrame index

                # Add the CSV content from the buffer to the zip file
                # The file name inside the zip will be df_name.csv
                zf.writestr(f"{trade_details_file_name}", csv_buffer.getvalue())
                strategy_obj.signal_trade_details[trade_id] = trade_details
        signal_trade_df.insert(0, column='trade_id', value=trade_id_list)
        """

