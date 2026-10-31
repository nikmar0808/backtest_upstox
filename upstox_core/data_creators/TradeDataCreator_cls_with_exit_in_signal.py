import os
from io import StringIO
from zipfile import ZipFile
from datetime import datetime
import logging, math, time, uuid
import pandas as pd
import pandas_ta as pta
import numpy as np
from backtest_common import __backtestconfig__
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
        self.trade_data_details_dir = __backtestconfig__.TRADE_DATA_DETAILS_DIR
        self.trade_data_handler_v3=HistoryDataAPIs()
        self.configuration = upstox_client.Configuration()
        self.configuration.access_token = __backtestconfig__.access_token

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
        
        if strategy_id == "NIFTY_S01":

            if not os.path.isfile(signal_file):
                print(f"{str(datetime.now())} Signal File {strategy_obj.signal_file} for Strategy {strategy_obj.strategy_id} not found")
                self.logger.exception(f"Trade Data Creator loading exception: File not found {signal_file}")
                raise FileNotFoundError(f"Trade Data Creator loading error: File not found {signal_file}")

        elif strategy_id == "NIFTY_S02":

            if not os.path.isfile(signal_file):
                print(f"{str(datetime.now())} Signal File {strategy_obj.signal_file} for Strategy {strategy_obj.strategy_id} not found")
                self.logger.exception(f"Trade Data Creator loading exception: File not found {signal_file}")
                raise FileNotFoundError(f"Trade Data Creator loading error: File not found {signal_file}")

        elif strategy_id in ['NIFTY_S03']:

            if not os.path.isfile(signal_file):
                print(f"{str(datetime.now())} Signal File {strategy_obj.signal_file} for Strategy {strategy_obj.strategy_id} not found")
                self.logger.exception(f"Trade Data Creator loading exception: File not found {signal_file}")
                raise FileNotFoundError(f"Trade Data Creator loading error: File not found {signal_file}")

            self.df_signal_data = pd.read_csv(signal_file, \
                                              dtype={'candle_sttime': str, 'open': float, 'high': float, 'low': float, 'close': float, 'vol': float, \
                                                     'ema_val': float, 'rma_ema_val': float, 'atr_tsl_long': float, \
                                                        'is_entry_trigger': bool, 'is_entry_filter': bool, \
                                                            'buy_strike': float, 'buy_strike_expiry': str, 'buy_strike_expiry_type': str, 'buy_strike_right': str, \
                                                                'instrument_key': str, 'trading_symbol': str, 'lot_size': int, 'freeze_quantity': int})
            if self.df_signal_data.empty:
                self.logger.exception(f"Trade Data Creator loading exception: Signal File is empty {signal_file}")
                raise ValueError(f"Trade Data Creator loading error: Signal File is empty {signal_file}")
            
            list_of_trades_for_strategy = self.create_list_of_trades_for_strategy(self.df_signal_data, strategy_obj)
            #print(f"{str(datetime.now())} Created list of trades for Strategy {strategy_id} - {list_of_trades_for_strategy}")

        elif strategy_id in ['NIFTY_S04']:

            if not os.path.isfile(signal_file):
                print(f"{str(datetime.now())} Signal File {strategy_obj.signal_file} for Strategy {strategy_obj.strategy_id} not found")
                self.logger.exception(f"Trade Data Creator loading exception: File not found {signal_file}")
                raise FileNotFoundError(f"Trade Data Creator loading error: File not found {signal_file}")

            self.df_signal_data = pd.read_csv(signal_file, \
                                              dtype={'candle_sttime': str, 'open': float, 'high': float, 'low': float, 'close': float, 'vol': float, \
                                                     'ema_val': float, 'rma_ema_val': float, 'atr_tsl_short': float, \
                                                        'is_entry_trigger': bool, 'is_entry_filter': bool, \
                                                            'buy_strike': float, 'buy_strike_expiry': str, 'buy_strike_expiry_type': str, 'buy_strike_right': str, \
                                                                'instrument_key': str, 'trading_symbol': str, 'lot_size': int, 'freeze_quantity': int})
            if self.df_signal_data.empty:
                self.logger.exception(f"Trade Data Creator loading exception: Signal File is empty {signal_file}")
                raise ValueError(f"Trade Data Creator loading error: Signal File is empty {signal_file}")

            list_of_trades_for_strategy = self.create_list_of_trades_for_strategy(self.df_signal_data, strategy_obj)
            #print(f"{str(datetime.now())} Created list of trades for Strategy {strategy_id} - {list_of_trades_for_strategy}")

        elif strategy_id in ['NIFTY_S05']:

            if not os.path.isfile(signal_file):
                self.logger.exception(f"Trade Data Creator loading exception: File not found {signal_file}")
                print(f"{str(datetime.now())} Signal File {strategy_obj.signal_file} for Strategy {strategy_obj.strategy_id} not found")
                raise FileNotFoundError(f"Trade Data Creator loading error: File not found {signal_file}")

            self.df_signal_data = pd.read_csv(signal_file, \
                                              dtype={'candle_sttime': str, 'open': float, 'high': float, 'low': float, 'close': float, 'vol': float, \
                                                     'ema_val': float, 'rma_ema_val': float, 'atr_tsl_long': float, \
                                                        'is_entry_trigger': bool, 'is_entry_filter': bool, \
                                                            'buy_strike': float, 'buy_strike_expiry': str, 'buy_strike_expiry_type': str, 'buy_strike_right': str, \
                                                                'instrument_key': str, 'trading_symbol': str, 'lot_size': int, 'freeze_quantity': int})
            if self.df_signal_data.empty:
                self.logger.exception(f"Trade Data Creator loading exception: Signal File is empty {signal_file}")
                raise ValueError(f"Trade Data Creator loading error: Signal File is empty {signal_file}")

            list_of_trades_for_strategy = self.create_list_of_trades_for_strategy(self.df_signal_data, strategy_obj)
            #print(f"{str(datetime.now())} Created list of trades for Strategy {strategy_id} - {list_of_trades_for_strategy}")

        elif strategy_id in ['NIFTY_S06']:

            if not os.path.isfile(signal_file):
                print(f"{str(datetime.now())} Signal File {strategy_obj.signal_file} for Strategy {strategy_obj.strategy_id} not found")
                self.logger.exception(f"Trade Data Creator loading exception: File not found {signal_file}")
                raise FileNotFoundError(f"Trade Data Creator loading error: File not found {signal_file}")

            self.df_signal_data = pd.read_csv(signal_file, \
                                              dtype={'candle_sttime': str, 'open': float, 'high': float, 'low': float, 'close': float, 'vol': float, \
                                                     'ema_val': float, 'rma_ema_val': float, 'atr_tsl_short': float, \
                                                        'is_entry_trigger': bool, 'is_entry_filter': bool, \
                                                            'buy_strike': float, 'buy_strike_expiry': str, 'buy_strike_expiry_type': str, 'buy_strike_right': str, \
                                                                'instrument_key': str, 'trading_symbol': str, 'lot_size': int, 'freeze_quantity': int})
            if self.df_signal_data.empty:
                self.logger.exception(f"Trade Data Creator loading exception: Signal File is empty {signal_file}")
                raise ValueError(f"Trade Data Creator loading error: Signal File is empty {signal_file}")

            list_of_trades_for_strategy = self.create_list_of_trades_for_strategy(self.df_signal_data, strategy_obj)
            #print(f"{str(datetime.now())} Created list of trades for Strategy {strategy_id} - {list_of_trades_for_strategy}")

        elif strategy_id in ['NIFTY_S07']:

            if not os.path.isfile(signal_file):
                self.logger.exception(f"Trade Data Creator loading exception: File not found {signal_file}")
                print(f"{str(datetime.now())} Signal File {strategy_obj.signal_file} for Strategy {strategy_obj.strategy_id} not found")
                raise FileNotFoundError(f"Trade Data Creator loading error: File not found {signal_file}")

            self.df_signal_data = pd.read_csv(signal_file, \
                                              dtype={'candle_sttime': str, 'open': float, 'high': float, 'low': float, 'close': float, 'vol': float, \
                                                     'ema_val': float, 'rma_ema_val': float, 'atr_tsl_long': float, \
                                                        'is_entry_trigger': bool, 'is_entry_filter': bool, \
                                                            'buy_strike': float, 'buy_strike_expiry': str, 'buy_strike_expiry_type': str, 'buy_strike_right': str, \
                                                                'instrument_key': str, 'trading_symbol': str, 'lot_size': int, 'freeze_quantity': int})
            if self.df_signal_data.empty:
                self.logger.exception(f"Trade Data Creator loading exception: Signal File is empty {signal_file}")
                raise ValueError(f"Trade Data Creator loading error: Signal File is empty {signal_file}")

            list_of_trades_for_strategy = self.create_list_of_trades_for_strategy(self.df_signal_data, strategy_obj)
            #print(f"{str(datetime.now())} Created list of trades for Strategy {strategy_id} - {list_of_trades_for_strategy}")

        elif strategy_id in ['NIFTY_S08']:

            if not os.path.isfile(signal_file):
                print(f"{str(datetime.now())} Signal File {strategy_obj.signal_file} for Strategy {strategy_obj.strategy_id} not found")
                self.logger.exception(f"Trade Data Creator loading exception: File not found {signal_file}")
                raise FileNotFoundError(f"Trade Data Creator loading error: File not found {signal_file}")

            self.df_signal_data = pd.read_csv(signal_file, \
                                              dtype={'candle_sttime': str, 'open': float, 'high': float, 'low': float, 'close': float, 'vol': float, \
                                                     'ema_val': float, 'rma_ema_val': float, 'atr_tsl_short': float, \
                                                        'is_entry_trigger': bool, 'is_entry_filter': bool, \
                                                            'buy_strike': float, 'buy_strike_expiry': str, 'buy_strike_expiry_type': str, 'buy_strike_right': str, \
                                                                'instrument_key': str, 'trading_symbol': str, 'lot_size': int, 'freeze_quantity': int})
            if self.df_signal_data.empty:
                self.logger.exception(f"Trade Data Creator loading exception: Signal File is empty {signal_file}")
                raise ValueError(f"Trade Data Creator loading error: Signal File is empty {signal_file}")

            list_of_trades_for_strategy = self.create_list_of_trades_for_strategy(self.df_signal_data, strategy_obj)
            #print(f"{str(datetime.now())} Created list of trades for Strategy {strategy_id} - {list_of_trades_for_strategy}")

        signal_trade_df = pd.DataFrame(list_of_trades_for_strategy, columns=['trade_date', 'buy_datetime', 'sell_datetime', 'investment_amount', 'instrument_key', 'trading_symbol', \
                                                                              'lot_size', 'num_of_lots', 'overall_pnl', 'pnl_realized', 'max_unrealized_profit_during_trade', 'max_unrealized_loss_during_trade'])
        trade_id_list = []
        trade_details_df = pd.DataFrame(list_of_trades_for_strategy, columns=['strategy_id', 'trade_instr_data'])

        strategy_obj.signal_trade_details = {}

        #Code to write Trade details files inside TradeDetails folder
        for index, row in trade_details_df.iterrows():
            trade_details = row['trade_instr_data']
            trade_id = f"{strategy_id}_{index+1}"
            trade_id_list.append(trade_id)
            trade_details_file_name = f"{trade_id}_Trade_Details_File.csv"
            trade_details_file = os.path.join(self.trade_data_details_dir, trade_details_file_name)

            with open(trade_details_file, "wt", newline='') as cfile:
                cfile.write(f"{trade_details.to_csv(index=False, header=True)}")
            print(f"{str(datetime.now())} Finished writing Trade Details File {trade_details_file} for strategy_id {strategy_id}")
            strategy_obj.signal_trade_details[trade_id] = trade_details
        signal_trade_df.insert(0, column='trade_id', value=trade_id_list)

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

        print(f"{str(datetime.now())} Finished writing Trade Details Files for each trade in {signal_trade_file} for strategy_id {strategy_id}")

        strategy_obj.signal_trades = signal_trade_df
        with open(signal_trade_file, "wt", newline='') as cfile:
            cfile.write(f"{signal_trade_df.to_csv(index=False, header=True)}")
        print(f"{str(datetime.now())} Finished writing Signal Trade File {signal_trade_file} for strategy_id {strategy_id}")

        return

    def create_list_of_trades_for_strategy(self, df_signal_data, strategy_obj) -> list:
        strategy_id = strategy_obj.strategy_id
        signal_file = strategy_obj.signal_file
       
        print(f"{str(datetime.now())} Creating trade list for Strategy {strategy_id}")

        # Create a list to hold trade data
        trade_list = []
        
        # Create a dictionary to hold data for each signal and corresponding trade data
        signal_trade_data = {}

        # Ensure 'candle_sttime' is a datetime object
        df_signal_data['candle_sttime'] = pd.to_datetime(df_signal_data['candle_sttime'])
        signal_rows_drop_all_indices = []
        signal_rows_drop_unique_indices = []

        # Get configurable values from Strategy Object
        entry_cutoff_time = strategy_obj.__dict__.get('entry_cutoff')
        if isinstance(entry_cutoff_time, str):
            # Convert string to datetime.time object
            entry_cutoff_time = datetime.strptime(entry_cutoff_time, '%H:%M:%S').time()
        elif isinstance(entry_cutoff_time, datetime):
            # If it's already a datetime object, extract the time
            entry_cutoff_time = entry_cutoff_time.time()
        trade_feed_interval = strategy_obj.__dict__.get('trade_feed_interval')
        feed_interval_unit = strategy_obj.__dict__.get('feed_interval_unit')
        trade_feed_interval_exp = strategy_obj.__dict__.get('trade_feed_interval_exp')
        overall_pnl = 0.0
        # Iterate through the DataFrame to find rows with 'is_entry_filter' == True
        for i, row in df_signal_data.iterrows():
            # Logical Point to revert to; changing exit from entry filter to is_trade_open
            if row['is_entry_filter'] and not df_signal_data['is_trade_open'].shift(1).iloc[i]:
                #current_date = row['candle_sttime'].date()
                trade_date = row['candle_date']
                instr_key = row['instrument_key']
                trading_symbol = row['trading_symbol']
                investment_amount = row['investment_amount'] if 'investment_amount' in row else strategy_obj.__dict__.get('investment_amount')
                lot_size = row['lot_size'] if 'lot_size' in row else strategy_obj.__dict__.get('lot_size')
                expiry_type = row['buy_strike_expiry_type']
                # Create a new block of rows starting with the current row
                current_block_rows = [row]

                # Extract subsequent rows with the same date until the next 'is_entry_filter' or different date or entry_cutoff_time is reached
                for j in range(i + 1, len(df_signal_data)):
                    """
                    # Added is_entry_filter to handle case where is_trade_open has not changed to False but new entry condition is trigger
                    if df_signal_data.loc[j, 'is_entry_filter'] or \
                        df_signal_data.loc[j, 'candle_sttime'].date() != current_date or \
                            df_signal_data.loc[j, 'candle_sttime'].time() > entry_cutoff_time:
                        break
                    elif ~df_signal_data.loc[j-1, 'is_trade_open']: # Added to handle case where is_trade_open is False
                        #current_block_rows.append(df_signal_data.loc[j-1])
                        break
                    """
                    if df_signal_data.loc[j-1, 'is_exit_trigger']:
                        break
                    current_block_rows.append(df_signal_data.loc[j])

                # Convert the block of rows to a DataFrame
                block_df = pd.DataFrame(current_block_rows).reset_index(drop=True)
                from_date = block_df['candle_sttime'].min().strftime('%Y-%m-%d')
                to_date = block_df['candle_sttime'].max().strftime('%Y-%m-%d')

                # If expiry_type is "current", Upstox API call requires interval and unit to be passed as two separate parameters "3" and "minutes"
                # If expiry_type is "expired", Upstox API call requires interval and unit to be passed together as "3minute"; note the string "minute" instead of "minutes"
                if (expiry_type == "current"):
                    trade_instr_data = self.trade_data_handler_v3.get_historical_candle_data1(
                        self.configuration, instr_key, feed_interval_unit, trade_feed_interval, to_date, from_date)
                elif (expiry_type == "expired"):                
                    trade_instr_data = self.trade_data_handler_v3.get_expired_historical_data(
                        self.configuration, instr_key, trade_feed_interval_exp, to_date, from_date)

                if len(trade_instr_data.data.candles) > 0:
                    trade_instr_data.data.candles.reverse()
                    my_columns = {'candle_sttime': str, 'open': float, 'high': float, 'low': float, 'close': float, 'vol': float, 'oi': float}
                    data_array = np.array(trade_instr_data.data.candles)

                    df = pd.DataFrame(data=data_array, columns=my_columns.keys()).astype(my_columns)
                    df.drop('oi', axis=1, inplace=True)

                    candle_sttime_col_index = df.columns.get_loc('candle_sttime')
                    df.loc[:, 'candle_sttime'] = pd.to_datetime(df['candle_sttime'], format='%Y-%m-%dT%H:%M:%S%z').dt.strftime('%Y-%m-%d %H:%M:%S')
                    candle_date = pd.to_datetime(df['candle_sttime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%Y-%m-%d')
                    df.insert(loc=candle_sttime_col_index + 1, column='candle_date', value=candle_date)

                    df_candle_sttime = pd.to_datetime(df['candle_sttime'], format='%Y-%m-%d %H:%M:%S')
                    block_df_candle_sttime = pd.to_datetime(block_df['candle_sttime'], format='%Y-%m-%d %H:%M:%S')

                    df = df[df_candle_sttime.isin(block_df_candle_sttime)]
                    df.reset_index(drop=True, inplace=True)

                    # Get the value of open price from the first row
                    #buy_price = df['open'].iloc[0] if not pd.isna(df['open'].iloc[0]) else 0.0
                    # Add 1 to the buy_price to account for at_market price slippage
                    buy_price = df['open'].iloc[0]+2 if not pd.isna(df['open'].iloc[0]) else 0.0
                    buy_datetime = df['candle_sttime'].iloc[0]

                    # Get the value of open price from the last row
                    #sell_price = df['open'].iloc[-1] if not pd.isna(df['open'].iloc[-1]) else 0.0
                    # Subtract 1 from the sell_price to account for at_market price slippage
                    sell_price = df['open'].iloc[-1]-2 if not pd.isna(df['open'].iloc[-1]) else 0.0
                    sell_datetime = df['candle_sttime'].iloc[-1]

                    # Add column with all values equal to the buy_price
                    df['buy_price'] = buy_price

                    # Calculate number of lots to trade
                    num_of_lots = self.calculate_lots_to_trade(investment_amount, buy_price, lot_size)

                    pnl_realized = round(((sell_price - buy_price) * lot_size * num_of_lots).astype(float), 2) if (sell_price > 0.0 and buy_price > 0.0) else 0.0

                    #df['pnl_unrealized'] = round(((df['close'] - df['buy_price']) * lot_size * num_of_lots).astype(float), 2)

                    # Update the last row of col3 with the last row's col1 value
                    profit_condition = df['high'] > df['buy_price']
                    loss_condition = df['low'] <= df['buy_price']
                    df['max_profit_unrealized'] = 0.0
                    df.loc[profit_condition, 'max_profit_unrealized'] = round(((df['high'] - df['buy_price']) * lot_size * num_of_lots).astype(float), 2)
                    #df.loc[~profit_condition, 'max_profit_unrealized'] = 0.0
                    trade_data_creator_logger.info(f"Max Profit Potential df['max_profit_unrealized']: {df['max_profit_unrealized']}")
                    max_profit_potential = df['max_profit_unrealized'].max()
                    trade_data_creator_logger.info(f"Max Profit Potential max_profit_potential: {max_profit_potential}")
                    if pd.isna(max_profit_potential):
                        max_profit_potential = 0.0
                    
                    df['max_loss_unrealized'] = 0.0
                    df.loc[loss_condition, 'max_loss_unrealized'] = round(((df['low'] - df['buy_price']) * lot_size * num_of_lots).astype(float), 2)
                    #df.loc[~loss_condition, 'max_loss_unrealized'] = 0.0
                    trade_data_creator_logger.info(f"Max Loss Potential df['max_loss_unrealized']: {df['max_loss_unrealized']}")
                    max_loss_potential = df['max_loss_unrealized'].min()
                    trade_data_creator_logger.info(f"Max Profit Potential max_loss_potential: {max_loss_potential}")
                    if pd.isna(max_loss_potential):
                        max_loss_potential = 0.0
                    
                    overall_pnl += pnl_realized

                    #trade_id = self.generate_unique_id()

                    #signal_trade_data = {'trade_date': trade_date, 'pnl_realized': pnl_realized, 'instrument_key': instr_key, 'trading_symbol': trading_symbol, 'signal_data': block_df, 'trade_instr_data': df}
                    """
                    signal_trade_data = {'trade_id': trade_id, 'trade_date': trade_date, 'investment_amount': investment_amount, 'trading_symbol': trading_symbol, 'num_of_lots': num_of_lots, \
                                         'overall_pnl': overall_pnl, 'pnl_realized': pnl_realized, 'max_unrealized_profit_during_trade': max_profit_potential, 'max_unrealized_loss_during_trade': max_loss_potential, \
                                            'trade_instr_data': df.to_dict(orient='records')}
                    """
                    signal_trade_data = {'trade_date': trade_date, 'buy_datetime': buy_datetime, 'sell_datetime': sell_datetime, 'instrument_key': instr_key, 'investment_amount': investment_amount, 'trading_symbol': trading_symbol, 'lot_size': lot_size,'num_of_lots': num_of_lots, \
                                         'overall_pnl': overall_pnl, 'pnl_realized': pnl_realized, 'max_unrealized_profit_during_trade': max_profit_potential, 'max_unrealized_loss_during_trade': max_loss_potential, 'strategy_id': strategy_id, 'trade_instr_data': df}

                    # Append the DataFrame to the list
                    trade_list.append(signal_trade_data)
                else:
                    print(f"{str(datetime.now())} No trade instrument data found for {instr_key} from {from_date} to {to_date}")
                    trade_data_creator_logger.debug(f"{str(datetime.now())} No trade instrument data found for {instr_key} from {from_date} to {to_date}")
                    signal_rows_drop_all_indices.extend(df_signal_data[df_signal_data['candle_date'] == from_date].index.tolist())
                    #signal_rows_drop_indices.append(df_signal_data[df_signal_data['candle_date'] == from_date].index)

            else:
                trade_data_creator_logger.debug(f"{str(datetime.now())} Skipping row {i} as is_entry_filter is False")
        if signal_rows_drop_all_indices:

            signal_rows_drop_unique_indices = list(set(signal_rows_drop_all_indices))
            df_signal_data.drop(signal_rows_drop_unique_indices, inplace=True)
            df_signal_data.reset_index(drop=True, inplace=True)
            trade_data_creator_logger.debug(f"{str(datetime.now())} Removing Signal data from Signal File for strategy_id {strategy_obj.strategy_id}")
            # Write the updated DataFrame back to the signal file          
            with open(signal_file, "wt", newline='') as cfile:
                cfile.write(df_signal_data.to_csv(index=False, header=True))
            print(f"{str(datetime.now())} No trade instrument data found for {instr_key} from {from_date} to {to_date}")
            print(f"{str(datetime.now())} Finished Removing Signal data from Signal File {signal_file} for strategy_id {strategy_obj.strategy_id}")
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
"""
self.trade_instr_details = {
    'symbol': self.df_hist_data['symbol'].iloc[0],
    'expiry': self.df_hist_data['expiry'].iloc[0],
    'strike': self.df_hist_data['buy_strike'].iloc[0],
    'option_type': 'CE' if self.df_hist_data['buy_strike_right'].iloc[0] == 'CE' else 'PE'
}
self.trade_instr_details['lot_size'] = self.__dict__.get('lot_size')
self.trade_instr_details['stop_loss'] = self.__dict__.get('stop_loss')
self.trade_instr_details['take_profit'] = self.__dict__.get('take_profit')
self.trade_instr_details['order_type'] = 'LIMIT'
self.trade_instr_details['price'] = self.__dict__.get('price')
self.trade_instr_details['trigger_price'] = self.__dict__.get('trigger_price')
"""
