import sys, os
from datetime import datetime, date, timedelta
import calendar
import upstox_client
from datetime import datetime
from backtest_common import __backtestconfig__
from upstox_core.data_creators.HistoryDataAPIs_cls import HistoryDataAPIs
import logging
import pandas as pd
import numpy as np


# Create and configure logger
history_data_creator_logger = logging.getLogger("logs/history_data_creator.log")
history_data_creator_logger.addHandler(logging.FileHandler("logs/history_data_creator.log", mode='a'))
history_data_creator_logger.setLevel(logging.INFO)

class HistoryDataCreator:

    def __init__(self,broker,logger=history_data_creator_logger): 
        self.broker=broker
        self.logger=logger
        self.history_data_years = __backtestconfig__.HISTORY_DATA_YEARS
        self.history_data_raw_file_dir = __backtestconfig__.HISTORY_DATA_RAW_FILE_DIR
        self.history_data_proc_file_dir = __backtestconfig__.HISTORY_DATA_PROC_FILE_DIR
        self.exp_inst_scrip_master_file_dir = __backtestconfig__.EXP_INST_SCRIP_MASTER_FILE_DIR
        self.exp_inst_nf_expiries_file = __backtestconfig__.EXP_INST_NF_EXPIRIES_FILE
        self.exp_inst_bnf_expiries_file = __backtestconfig__.EXP_INST_BNF_EXPIRIES_FILE

        self.history_data_handler_v3=HistoryDataAPIs()
        self.configuration = upstox_client.Configuration()
        # self.configuration.access_token = __backtestconfig__.access_token
        self.configuration.access_token = os.environ.get("UPSTOX_ACCESS_TOKEN", "")

    def get_history_data_from_to_dates(self, history_data_raw_file):
        
        if os.path.exists(history_data_raw_file):
            df = pd.read_csv(history_data_raw_file, usecols=['candle_sttime'])
            #print(f'df \n{df}')
            if (df.iloc[-1, 0]):
                last_date_in_file = df.iloc[-1, 0]
                #print(f'Last Date in Main File {last_date_in_file}')
            if not df.empty:
                df = None
                print(f"{str(datetime.now())} Size of df after clear {sys.getsizeof(df)/1000000} Mbytes in get_history_data_from_to_dates")
            #last_row_year
            #last_row_month
            
            print(f'{str(datetime.now())} History data file has data till {last_date_in_file}... if just a few days of data needs to be added, it should not take too long')

            try:
                past_date_start = datetime.strptime(last_date_in_file, '%Y-%m-%d %H:%M:%S') + timedelta(days=1)
                print(f"{str(datetime.now())} Past Date Start {past_date_start}")
            except ValueError:
                return "Invalid date format. Please use 'YYYY-MM-DD'."

            today = date.today()
            all_dates = []

            start_year = past_date_start.year
            start_month = past_date_start.month
            year = past_date_start.year
            month = past_date_start.month

            while True:
                # Get the number of days in the current month and year
                _, num_days = calendar.monthrange(year, month)
                if year == start_year and month == start_month:
                    month_start_date = past_date_start.date()
                else:
                    month_start_date = date(year, month, 1)
                
                month_end_date = date(year, month, num_days)

                # Ensure we don't go beyond today's date
                if month_start_date > today:
                    break
                if month_end_date > today:
                    month_end_date = today

                all_dates.append({
                    'year': year,
                    'month': calendar.month_name[month],
                    'monthStart': month_start_date.strftime('%Y-%m-%d'),
                    'monthEnd': month_end_date.strftime('%Y-%m-%d')
                })

                # Move to the next month
                if month == 12:
                    month = 1
                    year += 1
                else:
                    month += 1

                # Break if the next month would be beyond today's year and month
                if year > today.year or (year == today.year and month > today.month):
                    break

            l = pd.DataFrame(all_dates)
        else:
            print('History data file does not exist.. writing 1min, 3min and 5min interval data will take a few minutes, others should be quick')

            #years = ["2022", "2023", "2024", "2025"]
            # While historical data is available in Upstox from 2022, Expiry Data is available only from Oct 2024
            years = __backtestconfig__.HISTORY_DATA_YEARS
            nMonths = 12
            current_year = datetime.now().year
            current_month = datetime.now().month
            all_dates = []
            for year in years:
                if year == str(current_year) and current_month < nMonths:
                    nMonths = current_month
                # Generate month start dates using 'MS' frequency alias
                month_starts = pd.date_range(start=f'{year}-01-01', periods=nMonths, freq='MS')
                
                # Generate month end dates using 'ME' frequency alias
                month_ends = pd.date_range(start=f'{year}-01-01', periods=nMonths, freq='ME')

                for i in range(nMonths):
                    all_dates.append({
                        'year': year,
                        'month': month_starts[i].month_name(),
                        'monthStart': month_starts[i].strftime('%Y-%m-%d'),
                        'monthEnd': month_ends[i].strftime('%Y-%m-%d')
                    })
                    
            l = pd.DataFrame(all_dates)
        return l

    # Get historical data for a given instrument key, interval, and unit for a monthly range of dates
    def get_historical_data(self, instrument_key, interval, unit, from_date=None, to_date=None) -> pd.DataFrame:
        if not from_date or not to_date:
            return pd.DataFrame()
        my_columns = {'candle_sttime': str, 'open': float, 'high': float, 'low': float, 'close': float, 'vol': float, 'oi': float}
        print(f"{str(datetime.now())} Fetching Historical candle data from {from_date} to {to_date}")
        # Get historical candle data
        historical_candle_data = self.history_data_handler_v3.get_historical_candle_data(
            self.configuration, instrument_key, unit, interval, to_date, from_date)
        if not historical_candle_data or not historical_candle_data.data or not historical_candle_data.data.candles:
            print(f"{str(datetime.now())} No historical candle data found for {instrument_key} in {interval} {unit} interval from {from_date} to {to_date}")
            return pd.DataFrame()
        """
        history_data_creator_logger.info(f"{str(datetime.now())} Size of df before loop {sys.getsizeof(df)/1000000} Mbytes")
        history_data_creator_logger.info(f"{str(datetime.now())} Size of dataframes_to_concat before loop {sys.getsizeof(dataframes_to_concat)/1000000} Mbytes")
        history_data_creator_logger.info(f"{str(datetime.now())} Size of date_list before loop {sys.getsizeof(date_list)/1000000} Mbytes")
        """
        historical_candle_data.data.candles.reverse()
        
        data_array = np.array(historical_candle_data.data.candles)
        df = pd.DataFrame(data=data_array, columns=my_columns.keys()).astype(my_columns)
        df.drop('vol', axis=1, inplace=True)
        df.drop('oi', axis=1, inplace=True)
        #df = df.astype({'candle_sttime':'str', 'open':'float64', 'high':'float64', 'low':'float64', 'close':'float64'})

        return df

    def remove_repeat_rows(self, df, iteration_count=1):
        mask = df['candle_sttime'] <= df['candle_sttime'].shift(1)
        df.loc[:, 'is_candle_sttime_repeated'] = mask
        #history_data_creator_logger.info(f"{str(datetime.now())} Mask in iteration_count {iteration_count} \n{mask}")
        #history_data_creator_logger.info(f"{str(datetime.now())} Size of df before drop {sys.getsizeof(df)/1000000} Mbytes")
        true_count = len(df[df['is_candle_sttime_repeated'] == True])
        #history_data_creator_logger.info(f"{str(datetime.now())} True count {true_count}")

        if true_count and true_count > 0:
            indices_to_drop = df[df.is_candle_sttime_repeated == True].index
            # Remove rows with is_candle_sttime_repeated = True
            #history_data_creator_logger.info(f"{str(datetime.now())} indices_to_drop \n{indices_to_drop}")
            #history_data_creator_logger.info(f"{str(datetime.now())} Length before drop \n{len(df)}")
            df.drop(indices_to_drop, axis=0, inplace=True)
            df.reset_index(drop=True, inplace=True)
            #history_data_creator_logger.info(f"{str(datetime.now())} Length after drop and index reset \n{len(df)}")
            #return self.remove_repeat_rows(df)
            self.remove_repeat_rows(df, iteration_count + 1)
            return df
        else:
            history_data_creator_logger.info(f"{str(datetime.now())} Removed repeated rows.. Data cleanup done")
            return df

    def get_history_data_file_name(self, instrument_key, interval, unit):
        if instrument_key == "NSE_INDEX|Nifty 50" and unit == "minutes":
            return f"Nifty_HistoryData_{interval}m.csv"
        elif instrument_key == "NSE_INDEX|Nifty 50" and unit == "days":
            return f"Nifty_HistoryData_daily.csv"
        elif instrument_key == "NSE_INDEX|Nifty 50" and unit == "weeks":
            return f"Nifty_HistoryData_weekly.csv"
        elif instrument_key == "NSE_INDEX|Nifty Bank" and unit == "minutes":
            return f"BankNifty_HistoryData_{interval}m.csv"
        elif instrument_key == "NSE_INDEX|Nifty Bank" and unit == "days":
            return f"BankNifty_HistoryData_daily.csv"
        elif instrument_key == "NSE_INDEX|Nifty Bank" and unit == "weeks":
            return f"BankNifty_HistoryData_weekly.csv"        
        return None

    def write_historical_data_to_raw_file(self, instrument_key, interval, unit):
        print(f"{str(datetime.now())} Fetching Historical candle data to create raw file for {instrument_key} in {interval} {unit} interval")
        file_name = self.get_history_data_file_name(instrument_key, interval, unit)
        if file_name:
            history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, file_name)
            history_data_proc_file = os.path.join(__backtestconfig__.HISTORY_DATA_PROC_FILE_DIR, file_name)
        else:
            raise ValueError(f"Invalid instrument_key: {instrument_key} or interval: {interval} or unit: {unit}")

        l = self.get_history_data_from_to_dates(history_data_raw_file)
        #print(l)

        # Create in main file if history data file does not exist
        if not os.path.exists(history_data_raw_file):
            file_mode = 'a' # change of year causes append mode to create incorrect data
            write_count = 1
            for year, year_df in l.groupby('year'):
                dataframes_to_concat = []
                df = pd.DataFrame()
                df_from_file = pd.DataFrame()
                #if file_mode == 'a':

                if os.path.exists(history_data_raw_file):
                    df_from_file = pd.read_csv(history_data_raw_file, dtype={'candle_sttime':str, 'open':float, 'high':float, 'low':float, 'close':float, 'vol':float})
                    dataframes_to_concat.append(df_from_file.tail(1)) # remove this row after recursive check is finished

                print(f"{str(datetime.now())} Fetching Historical candle data for {year}")

                # Historical data is availabe only from 1st Jan 2022 and for a maximum of 30 days for 1m, 3m and 15m intervals.
                for month, from_date, to_date in zip(year_df["month"], year_df["monthStart"], year_df["monthEnd"]):
                    print(f"{str(datetime.now())} Fetching Historical candle data for {month}")
                    # Get historical candle data
                    df = self.get_historical_data(instrument_key, interval, unit, from_date, to_date)
                    df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3
                    dataframes_to_concat.append(df)
                if dataframes_to_concat:
                    df = pd.concat(dataframes_to_concat, ignore_index=True)
                    dataframes_to_concat.clear()
                else:
                    print(f"{str(datetime.now())} No historical candle data found for {instrument_key} in {interval} {unit} interval")
                    return
                
                sys.setrecursionlimit(15000)
                
                print(f"{str(datetime.now())} Size of df before remove_repeat_rows {sys.getsizeof(df)/1000000} Mbytes")

                # Remove rows for timestamps which already have rows in the Dataframe
                df = self.remove_repeat_rows(df)
                print(f"{str(datetime.now())} After remove_repeat_rows")

                # Remove the first row (last row of previous year added for removal of repeated rows)
                df = df.iloc[1:].copy()

                # Remove mask column from the Dataframe
                df.drop('is_candle_sttime_repeated', axis=1, inplace=True)

                print(f"{str(datetime.now())} Writing historical candle data to temporary file for {year}")
                # Write the DataFrame to the history data file
                with open(history_data_raw_file, file_mode, newline='') as file:
                    if write_count == 1:
                        file.write(df.to_csv(index=False, header=True))
                    else:
                        file.write(df.to_csv(index=False, header=False))
                print(f"{str(datetime.now())} Finished creating temporary Historical candle data file for {instrument_key} in {interval} {unit} interval")

                # To ensure headers are not written to the file on subsequent writes
                write_count += 1
            
                if not df.empty:
                    df = None
                    print(f"{str(datetime.now())} Size of df after clear {sys.getsizeof(df)/1000000} Mbytes")

                if not df_from_file.empty:
                    df_from_file = None
                    print(f"{str(datetime.now())} Size of df_from_file after clear {sys.getsizeof(df)/1000000} Mbytes")

            print(f"{str(datetime.now())} Writing historical candle data to file for {year}")
            # Calculate indicators to keep memory footprint smaller for 1 min interval in particular
            df_from_file = pd.DataFrame()

            df_from_file = pd.read_csv(history_data_raw_file, dtype={'candle_sttime':str, 'open':float, 'high':float, 'low':float, 'close':float, 'vol':float})

            # Overwrite file with data along with indicators
            file_mode = 'w'

            df_from_file.loc[:, 'candle_sttime'] = pd.to_datetime(df_from_file['candle_sttime'], format='%Y-%m-%dT%H:%M:%S%z').dt.strftime('%Y-%m-%d %H:%M:%S')
            df_from_file.drop_duplicates(inplace=True)
            df_from_file.reset_index(drop=True, inplace=True)

            with open(history_data_raw_file, file_mode, newline='') as file:
                file.write(df_from_file.to_csv(index=False, header=True))
            print(f"{str(datetime.now())} Finished creating temporary Historical candle data file for {instrument_key} in {interval} {unit} interval")
            
            if not df_from_file.empty:
                df_from_file = None
                print(f"{str(datetime.now())} Size of df_from_file after clear {sys.getsizeof(df_from_file)/1000000} Mbytes")
        # Write in temporary file and append to main history data file if it exists
        else:
            temp_file_name = f"HistoryData_{interval}m_temp.csv"
            temp_history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, temp_file_name)
            file_mode = 'a' # change of year causes append mode to create incorrect data
            write_count = 1
            df_from_main_file = pd.read_csv(history_data_raw_file, dtype={'candle_sttime':str, 'open':float, 'high':float, 'low':float, 'close':float, 'vol':float})
            if (df_from_main_file.iloc[-1, 0]):
                last_date_in_file = df_from_main_file.iloc[-1, 0]
            hist_data_already_fetched = False
            for year, year_df in l.groupby('year'):
                dataframes_to_concat = []
                df = pd.DataFrame()
                df_from_temp_file = pd.DataFrame()

                #Add last row from temp file only once 
                if os.path.exists(temp_history_data_raw_file):
                    df_from_temp_file = pd.read_csv(temp_history_data_raw_file, dtype={'candle_sttime':str, 'open':float, 'high':float, 'low':float, 'close':float, 'vol':float})
                    dataframes_to_concat.append(df_from_temp_file.tail(1)) # remove this row after recursive check is finished
                #Add last row from main file only once 
                else:
                    dataframes_to_concat.append(df_from_main_file.tail(1)) # remove this row after recursive check is finished
                    
                print(f"{str(datetime.now())} Fetching Historical candle data for {year}")

                # Historical data is available only from 1st Jan 2022 and for a maximum of 30 days for 1m, 3m and 15m intervals.
                for month, from_date, to_date in zip(year_df["month"], year_df["monthStart"], year_df["monthEnd"]):
                    print(f"{str(datetime.now())} Fetching Historical candle data for {month}")
                    # Get historical candle data
                    df = self.get_historical_data(instrument_key, interval, unit, from_date, to_date)
                    df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3

                    last_date_from_df = (pd.to_datetime(df.tail(1)['candle_sttime'], format='%Y-%m-%dT%H:%M:%S%z').dt.strftime('%Y-%m-%d %H:%M:%S')).values[0]

                    if last_date_in_file and last_date_from_df and last_date_from_df == last_date_in_file:
                        hist_data_already_fetched = True
                        break
                    dataframes_to_concat.append(df)
                if hist_data_already_fetched:
                    break
                if dataframes_to_concat:
                    df = pd.concat(dataframes_to_concat, ignore_index=True)
                    dataframes_to_concat.clear()
                else:
                    print(f"{str(datetime.now())} No historical candle data found for {instrument_key} in {interval} {unit} interval")
                    return
                
                sys.setrecursionlimit(15000)
                
                print(f"{str(datetime.now())} Size of df before remove_repeat_rows {sys.getsizeof(df)/1000000} Mbytes")

                # Remove rows for timestamps which already have rows in the Dataframe
                df = self.remove_repeat_rows(df)
                print(f"{str(datetime.now())} After remove_repeat_rows")

                # Remove the first row (last row of previous year/file added for removal of repeated rows)
                df = df.iloc[1:].copy()

                # Remove mask column from the Dataframe
                df.drop('is_candle_sttime_repeated', axis=1, inplace=True)

                print(f"{str(datetime.now())} Writing historical candle data to temporary file for {year}")
                # Write the DataFrame to the history data file
                with open(temp_history_data_raw_file, file_mode, newline='') as file:
                    if write_count == 1:
                        file.write(df.to_csv(index=False, header=True))
                    else:
                        file.write(df.to_csv(index=False, header=False))
                print(f"{str(datetime.now())} Finished creating temporary Historical candle data file for {instrument_key} in {interval} {unit} interval")

                # To ensure headers are not written to the file on subsequent writes
                write_count += 1
            
                if not df.empty:
                    df = None
                    print(f"{str(datetime.now())} Size of df after clear {sys.getsizeof(df)/1000000} Mbytes")

                if not df_from_temp_file.empty:
                    df_from_temp_file = None
                    print(f"{str(datetime.now())} Size of df_from_file after clear {sys.getsizeof(df)/1000000} Mbytes")

            if hist_data_already_fetched:
                print(f"{str(datetime.now())} Historical data up to date for {instrument_key} in {interval} {unit} interval for {year}")
                return
            print(f"{str(datetime.now())} Writing historical candle data to file for {year}")
            # Calculate indicators to keep memory footprint smaller for 1 min interval in particular
            df_from_temp_file = pd.DataFrame()

            df_from_temp_file = pd.read_csv(temp_history_data_raw_file, dtype={'candle_sttime':str, 'open':float, 'high':float, 'low':float, 'close':float, 'vol':float})

            # Overwrite file with data along with indicators
            file_mode = 'w'

            df_from_temp_file.loc[:, 'candle_sttime'] = pd.to_datetime(df_from_temp_file['candle_sttime'], format='%Y-%m-%dT%H:%M:%S%z').dt.strftime('%Y-%m-%d %H:%M:%S')
            df_final = pd.concat([df_from_main_file, df_from_temp_file], ignore_index=True)

            os.remove(temp_history_data_raw_file)
            df_final.drop_duplicates(inplace=True)
            df_final.reset_index(drop=True, inplace=True)
            
            with open(history_data_raw_file, file_mode, newline='') as file:
                file.write(df_final.to_csv(index=False, header=True))
            print(f"{str(datetime.now())} Finished creating temporary Historical candle data file for {instrument_key} in {interval} {unit} interval")
            
            if not df_from_main_file.empty:
                df_from_main_file = None
                print(f"{str(datetime.now())} Size of df_from_main_file after clear {sys.getsizeof(df_from_main_file)/1000000} Mbytes")
            if not df_from_temp_file.empty:
                df_from_temp_file = None
                print(f"{str(datetime.now())} Size of df_from_temp_file after clear {sys.getsizeof(df_from_temp_file)/1000000} Mbytes")
            if not df_final.empty:
                df_final = None
                print(f"{str(datetime.now())} Size of df_final after clear {sys.getsizeof(df_final)/1000000} Mbytes")

        return
        """
        print(f"{str(datetime.now())} Before calculate_indicators")

        # Calculate indicators for all rows in the Dataframe
        df_from_file = self.calculate_indicators(df_from_file, interval, unit)
        print(f"{str(datetime.now())} After calculate_indicators")
        """

    # Get Expired Contracts for an instrument key
    def get_expired_expiries(self, expired_instrument_key) -> pd.DataFrame:
        if expired_instrument_key not in ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank"]:
            print(f"{str(datetime.now())} Invalid instrument key {expired_instrument_key} for fetching expiries")
            return pd.DataFrame()
        #my_columns = ['exchange', 'exchange_token', 'expiry', 'freeze_quantity', 'instrument_key', 'instrument_type', 'lot_size', 'minimum_lot', 'name', 'segment', 'strike_price', 'tick_size', 'trading_symbol', 'underlying_key', 'underlying_symbol', 'underlying_type', 'weekly']
        print(f"{str(datetime.now())} Fetching Expiries for {expired_instrument_key}")

        expiries = self.history_data_handler_v3.get_expiries(self.configuration, expired_instrument_key)
        
        if not expiries or not expiries.data:
            print(f"{str(datetime.now())} No Expiries found for {expired_instrument_key}")
            return

        if expired_instrument_key == "NSE_INDEX|Nifty 50":
            file_name = os.path.join(self.exp_inst_scrip_master_file_dir, self.exp_inst_nf_expiries_file)
        elif expired_instrument_key == "NSE_INDEX|Nifty Bank":
            file_name = os.path.join(self.exp_inst_scrip_master_file_dir, self.exp_inst_bnf_expiries_file)

        df = pd.DataFrame(expiries.data, columns=['expiry'])
        df_temp = pd.DataFrame()
        # Convert the 'expiry' string column to datetime objects
        df_temp['expiry'] = pd.to_datetime(df['expiry'])
        df_temp.sort_values(by='expiry', ascending=True, inplace=True)
        df_temp.reset_index(drop=True, inplace=True)

        # Extract year and month for grouping
        df_temp['year_month'] = df_temp['expiry'].dt.to_period('M')

        # Find the max of dates available for each month, this will be the monthly expiry, the rest being weekly 
        df_temp['max_date_in_month'] = df_temp.groupby('year_month')['expiry'].transform('max')

        # Set the 'weekly' flag to True or False
        df_temp['weekly'] = (df_temp['expiry'] != df_temp['max_date_in_month'])

        df['weekly'] = df_temp['weekly']
        df['expiry_type'] = "expired"

        with open(file_name , 'w', newline='') as file:
            file.write(df.to_csv(index=False, header=True))
        print(f"{str(datetime.now())} Finished writing Expired Contract expiry dates to file {file_name}")
        return df

    # Get Expired Contracts for an instrument key and an expiry date
    def get_expired_option_contracts(self, expired_instrument_key, expiries=None):
        my_columns = {'exchange' : str, 'exchange_token' : str, 'expiry' : str, 'freeze_quantity' : int, 'instrument_key' : str, 'instrument_type' : str, 'lot_size' : int, 'minimum_lot' : int, 'name' : str, 'segment' : str, 'strike_price' : int, 'tick_size' : int, 'trading_symbol' : str, 'underlying_key' : str, 'weekly' : bool}
        print(f"{str(datetime.now())} Fetching Expired Contracts for {expired_instrument_key}")
        # Get historical candle data

        for expiry_date in expiries['expiry']:

            if expired_instrument_key == "NSE_INDEX|Nifty 50":
                self.expired_opt_contracts_file = os.path.join(self.exp_inst_scrip_master_file_dir, f"Exp_Opt_Contracts_Nf_{expiry_date}_Scripmaster.csv")
            elif expired_instrument_key == "NSE_INDEX|Nifty Bank":
                self.expired_opt_contracts_file = os.path.join(self.exp_inst_scrip_master_file_dir, f"Exp_Opt_Contracts_Bnf_{expiry_date}_Scripmaster.csv")
            
            if os.path.exists(self.expired_opt_contracts_file):
                print(f"{str(datetime.now())} Expired Option Contracts file {self.expired_opt_contracts_file} already exists for {expired_instrument_key} for Expiry Date {expiry_date}")
                continue
            
            expired_options_contracts_data = []
            expired_options_contracts = []
            expired_options_contracts_data = self.history_data_handler_v3.get_expired_option_contracts(
                self.configuration, expired_instrument_key, expiry_date)
            if not expired_options_contracts_data:
                print(f"{str(datetime.now())} No Expired Option Contracts found for {expired_instrument_key} for Expiry Date {expiry_date}")
            
            #print(f"{str(datetime.now())} expired_options_contracts_data.data {expired_options_contracts_data.data}")

            for contract in expired_options_contracts_data.data:
                df = pd.DataFrame(contract.to_dict(), index=[0], columns=my_columns.keys()).astype(my_columns)
                df.dropna(axis=1, how='all', inplace=True)
                if not df.empty:
                    expired_options_contracts.append(pd.DataFrame(df))
                    df = None

            df_contracts = pd.concat(expired_options_contracts, ignore_index=True)
            df_contracts.sort_values(by=['exchange_token'], inplace=True)
            
            if df_contracts.empty:
                print(f"{str(datetime.now())} No Expired Option Contracts found for {expired_instrument_key} for Expiry Date {expiry_date}")
                return
            
            print(f"{str(datetime.now())} Writing Expired Option Contracts to file {self.expired_opt_contracts_file}")
            
            with open(self.expired_opt_contracts_file, 'w', newline='') as file:
                file.write(df_contracts.to_csv(index=False, header=True))
            df_contracts = None
            expired_options_contracts = None
        
        return

    # Get Active Expiry Date for an instrument key
    # Skeleton for implementation, API method not yet available
    def get_active_expiries(self, active_instrument_key) -> pd.DataFrame:
        """
        if active_instrument_key not in ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank"]:
            print(f"{str(datetime.now())} Invalid instrument key {active_instrument_key} for fetching expiries")
            return pd.DataFrame()
        #my_columns = ['exchange', 'exchange_token', 'expiry', 'freeze_quantity', 'instrument_key', 'instrument_type', 'lot_size', 'minimum_lot', 'name', 'segment', 'strike_price', 'tick_size', 'trading_symbol', 'underlying_key', 'underlying_symbol', 'underlying_type', 'weekly']
        print(f"{str(datetime.now())} Fetching Expiries for {active_instrument_key}")

        expiries = self.history_data_handler_v3.get_expiries(self.configuration, active_instrument_key)
        if not expiries or not expiries.data:
            print(f"{str(datetime.now())} No Expiries found for {active_instrument_key}")
            return

        if active_instrument_key == "NSE_INDEX|Nifty 50":
            file_name = __upstoxconfig__.ACTIVE_INST_NF_EXPIRIES_FILE
        elif active_instrument_key == "NSE_INDEX|Nifty Bank":
            file_name = __upstoxconfig__.ACTIVE_INST_BNF_EXPIRIES_FILE
        df = pd.DataFrame(expiries.data, columns=['expiry'])
        with open(file_name , 'w', newline='') as file:
            file.write(df.to_csv(index=False, header=False))
        return df
        """
        return
