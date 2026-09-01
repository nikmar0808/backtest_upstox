from __future__ import print_function
import logging
from datetime import datetime, date
import os
import requests, gzip, logging, json
from backtest_common import __backtestconfig__
import pandas as pd

# Create and configure logger
scrip_master_logger = logging.getLogger("logs/scrip_master_apis.log")
scrip_master_logger.addHandler(logging.FileHandler("logs/scrip_master_apis.log", mode='a'))
scrip_master_logger.setLevel(logging.INFO)

class ScripMasterAPIs:

    def __init__(self,broker,logger=scrip_master_logger): 
        self.broker=broker
        self.logger=logger
        self.curr_inst_scrip_master_url = __backtestconfig__.CURR_INST_SCRIPT_MASTER_URL
        self.curr_inst_scrip_master_file_dir = __backtestconfig__.CURR_INST_SCRIP_MASTER_FILE_DIR
        self.curr_inst_scrip_master_gz_file = __backtestconfig__.CURR_INST_SCRIP_MASTER_JSON_GZ_FILE
        self.curr_inst_scrip_master_json_file = __backtestconfig__.CURR_INST_SCRIP_MASTER_JSON_FILE
        self.curr_inst_scrip_master_file_dir = __backtestconfig__.CURR_INST_SCRIP_MASTER_FILE_DIR
        self.curr_inst_scrip_master_fut_file = __backtestconfig__.CURR_INST_SCRIP_MASTER_NFO_INDEX_FUT_FILE
        self.curr_inst_scrip_master_nf_opt_file = __backtestconfig__.CURR_INST_SCRIP_MASTER_NF_OPT_FILE
        self.curr_inst_scrip_master_bnf_opt_file = __backtestconfig__.CURR_INST_SCRIP_MASTER_BNF_OPT_FILE
        self.curr_inst_nf_expiries_file = __backtestconfig__.CURR_INST_NF_EXPIRIES_FILE
        self.curr_inst_bnf_expiries_file = __backtestconfig__.CURR_INST_BNF_EXPIRIES_FILE
        self.exp_inst_script_master_file_dir = __backtestconfig__.EXP_INST_SCRIP_MASTER_FILE_DIR
        self.exp_inst_nf_expiries_file = __backtestconfig__.EXP_INST_NF_EXPIRIES_FILE
        self.exp_inst_bnf_expiries_file = __backtestconfig__.EXP_INST_BNF_EXPIRIES_FILE
        self.expiries_file_dir =  __backtestconfig__.EXPIRIES_FILE_DIR
        self.expiries_nf_file =  __backtestconfig__.EXPIRIES_NF_FILE
        self.expiries_bnf_file =  __backtestconfig__.EXPIRIES_BNF_FILE


    def get_scrip_master(self):

        try:
            with requests.Session() as s:
                with open(os.path.join(self.curr_inst_scrip_master_file_dir, self.curr_inst_scrip_master_gz_file), 'wb') as f_gz_out:
                    download_gz = s.get(self.curr_inst_scrip_master_url, stream=True)
                    f_gz_out.write(download_gz.content)
                    scrip_master_logger.info(f"Scripmaster JSON GZ Saved {os.path.join(self.curr_inst_scrip_master_file_dir, self.curr_inst_scrip_master_gz_file)}")
            with gzip.open(os.path.join(self.curr_inst_scrip_master_file_dir, self.curr_inst_scrip_master_gz_file), 'rt', encoding='utf-8') as gz:
                with open(os.path.join(self.curr_inst_scrip_master_file_dir, self.curr_inst_scrip_master_json_file), 'wt', encoding='utf-8') as f_json_out:
                    f_json_out.writelines(gz)
                    scrip_master_logger.info(f"Scripmaster JSON Saved {os.path.join(self.curr_inst_scrip_master_file_dir, self.curr_inst_scrip_master_json_file)}")
            my_columns = {'exchange' : str, 'exchange_token' : str, 'expiry' : int, 'freeze_quantity' : int, 'instrument_key' : str, 'instrument_type' : str, 'lot_size' : int, 'minimum_lot' : int, 'name' : str, 'segment' : str, 'strike_price' : int, 'tick_size' : int, 'trading_symbol' : str, 'underlying_key' : str, 'weekly' : bool}
            df = pd.read_json(os.path.join(self.curr_inst_scrip_master_file_dir, self.curr_inst_scrip_master_json_file))
            df_nfbnf_fut_rows = pd.DataFrame()
            df_nf_opt_rows = pd.DataFrame()
            df_bnf_opt_rows = pd.DataFrame()

            df_nfbnf_fut_rows = df.loc[(df['segment'] == "NSE_FO") & (df['name'].isin(["NIFTY", "BANKNIFTY"])) & (df['instrument_type'] == "FUT"), my_columns.keys()].astype(my_columns)
            df_nf_opt_rows = df.loc[(df['segment'] == "NSE_FO") & (df['name'] == "NIFTY") & (df['instrument_type'].isin(["CE", "PE"])), my_columns.keys()].astype(my_columns)
            df_bnf_opt_rows = df.loc[(df['segment'] == "NSE_FO") & (df['name'] == "BANKNIFTY") & (df['instrument_type'].isin(["CE", "PE"])), my_columns.keys()].astype(my_columns)

            df_nfbnf_fut_rows.sort_values(by=['exchange_token'], inplace=True)
            df_nf_opt_rows.sort_values(by=['exchange_token'], inplace=True)
            df_bnf_opt_rows.sort_values(by=['exchange_token'], inplace=True)

            df_nfbnf_fut_rows.reset_index(drop=True, inplace=True)
            df_nf_opt_rows.reset_index(drop=True, inplace=True)
            df_bnf_opt_rows.reset_index(drop=True, inplace=True)

            str_expiry_nfbnf_fut_rows = (pd.to_datetime(df_nfbnf_fut_rows['expiry'].astype(int), unit='ms').dt.strftime('%Y-%m-%d')).astype(str)
            str_expiry_nf_opt_rows = (pd.to_datetime(df_nf_opt_rows['expiry'].astype(int), unit='ms').dt.strftime('%Y-%m-%d')).astype(str)
            str_expiry_bnf_opt_rows = (pd.to_datetime(df_bnf_opt_rows['expiry'].astype(int), unit='ms').dt.strftime('%Y-%m-%d')).astype(str)

            df_nfbnf_fut_rows.drop('expiry', axis=1, inplace=True)
            df_nf_opt_rows.drop('expiry', axis=1, inplace=True)
            df_bnf_opt_rows.drop('expiry', axis=1, inplace=True)

            df_nfbnf_fut_rows.insert(2, 'expiry', str_expiry_nfbnf_fut_rows)
            df_nf_opt_rows.insert(2, 'expiry', str_expiry_nf_opt_rows)
            df_bnf_opt_rows.insert(2, 'expiry', str_expiry_bnf_opt_rows)

            file_path_fut = os.path.join(self.curr_inst_scrip_master_file_dir, self.curr_inst_scrip_master_fut_file)
            file_path_nf_opt = os.path.join(self.curr_inst_scrip_master_file_dir, self.curr_inst_scrip_master_nf_opt_file)
            file_path_bnf_opt = os.path.join(self.curr_inst_scrip_master_file_dir, self.curr_inst_scrip_master_bnf_opt_file)
                         
            with open(file_path_fut, 'w') as file:
                file.write(df_nfbnf_fut_rows.to_csv(index=False, header=True))
                print(f"{str(datetime.now())} Finished writing Current Futures Contracts to file {file_path_fut}")
            with open(file_path_nf_opt, 'w') as file:
                file.write(df_nf_opt_rows.to_csv(index=False, header=True))
                print(f"{str(datetime.now())} Finished writing Current Nifty Options Contracts to file {file_path_nf_opt}")
            with open(file_path_bnf_opt, 'w') as file:
                file.write(df_bnf_opt_rows.to_csv(index=False, header=True))
                print(f"{str(datetime.now())} Finished writing Current BankNifty Options Contracts to file {file_path_bnf_opt}")

            df = None
            df_nfbnf_fut_rows = None
            df_nf_opt_rows = None
            df_bnf_opt_rows = None
        except Exception as ex:
            print(f'Exception {ex}')
            scrip_master_logger.exception(f"Exeption in getting scrip master")
        return
    
    def get_instrument_key(self, trading_symbol_name, strike, instrument_type, expiry_date):
        
        instrument_key_srch_str = ""
        instrument_key = ""
        instrument_key_details = []
        trading_symbol_list = ['NIFTY', 'BANKNIFTY']
        fut_instrument_type_list = ['FUT']
        opt_instrument_type_list = ['CE', 'PE']

        if trading_symbol_name in trading_symbol_list:
            if  instrument_type in fut_instrument_type_list:
                instrument_key_srch_str = trading_symbol_name+" FUT "+expiry_date.strftime("%d %b %y").upper()
                print(f"Search inst key for {instrument_key_srch_str}")
                instrument_key = self.search_instr_token_in_json('trading_symbol', instrument_key_srch_str, self.file_path_fut)
                instrument_key_details = [instrument_key, instrument_key_srch_str]
            elif instrument_type in opt_instrument_type_list:
                instrument_key_srch_str = trading_symbol_name+ " " +strike+" "+instrument_type+" "+expiry_date.strftime("%d %b %y").upper()
                print(f"Search inst key for {instrument_key_srch_str}")
                instrument_key = self.search_instr_token_in_json('trading_symbol', instrument_key_srch_str, self.file_path_opt)
                instrument_key_details = [instrument_key, instrument_key_srch_str]
            else:
                raise TypeError("Invalid input type or value")
        else:
            raise TypeError("Invalid input type or value")
        return instrument_key_details
    
    def search_instr_token_in_json (self, column_name_to_search, value_to_match, file_path):
        instr_key = ""        
        with open(file_path, 'r') as f_json_in:
            rows = json.load(f_json_in)
            for row in rows:
                if(row['name'] == "NIFTY" and row['instrument_type'] == "FUT" and row[column_name_to_search] == value_to_match):
                    instr_key = row['instrument_key']
                    return instr_key
                elif(row['name'] == "BANKNIFTY" and row['instrument_type'] == "FUT" and row[column_name_to_search] == value_to_match):
                    instr_key = row['instrument_key']
                    return instr_key
                elif(row['name'] == "NIFTY" and row['instrument_type'] == "CE" and row[column_name_to_search] == value_to_match):
                    instr_key = row['instrument_key']
                    return instr_key
                elif(row['name'] == "NIFTY" and row['instrument_type'] == "PE" and row[column_name_to_search] == value_to_match):
                    instr_key = row['instrument_key']
                    return instr_key
                elif(row['name'] == "BANKNIFTY" and row['instrument_type'] == "CE" and row[column_name_to_search] == value_to_match):
                    instr_key = row['instrument_key']
                    return instr_key
                elif(row['name'] == "BANKNIFTY" and row['instrument_type'] == "PE" and row[column_name_to_search] == value_to_match):
                    instr_key = row['instrument_key']
                    return instr_key
        return instr_key

    def merge_exp_curr_expiry_dates(self, instrument_key):

        curr_expiries_file = ""
        expiries_file = ""
        if instrument_key == "NSE_INDEX|Nifty 50":
            exp_file = os.path.join(self.exp_inst_script_master_file_dir, self.exp_inst_nf_expiries_file)
            curr_file = os.path.join(self.curr_inst_scrip_master_file_dir, self.curr_inst_scrip_master_nf_opt_file)
            curr_expiries_file = os.path.join(self.curr_inst_scrip_master_file_dir, self.curr_inst_nf_expiries_file)
            expiries_file =  os.path.join(self.expiries_file_dir, self.expiries_nf_file)
        elif instrument_key == "NSE_INDEX|Nifty Bank":
            exp_file = os.path.join(self.exp_inst_script_master_file_dir, self.exp_inst_bnf_expiries_file)
            curr_file = os.path.join(self.curr_inst_scrip_master_file_dir, self.curr_inst_scrip_master_bnf_opt_file)
            curr_expiries_file = os.path.join(self.curr_inst_scrip_master_file_dir, self.curr_inst_bnf_expiries_file)
            expiries_file =  os.path.join(self.expiries_file_dir, self.expiries_bnf_file)

        # Define the columns to read and their data types
        columns_to_read = ['expiry', 'weekly', 'expiry_type']
        column_datatypes = {'expiry': str, 'weekly': bool, 'expiry_type': str}
        # Get expiry dates for expired contracts
        df_exp = pd.read_csv(exp_file, usecols=columns_to_read, dtype=column_datatypes)

        columns_to_read = ['expiry', 'weekly']
        column_datatypes = {'expiry': str, 'weekly': bool}

        # Get expiry dates for current contracts
        df_curr = pd.read_csv(curr_file, usecols=columns_to_read, dtype=column_datatypes)

        df_curr_dt = pd.DataFrame()
        df_curr_dt['expiry'], df_curr_dt['weekly'] = pd.to_datetime(df_curr['expiry'], format='%Y-%m-%d'), df_curr['weekly']
        df_curr_dt.sort_values(by='expiry', inplace=True)

        # Find unique 'expiry' dates in current expiry file
        df_unique_curr_expiry_dates = df_curr_dt.drop_duplicates(subset=['expiry', 'weekly'])
        df_unique_curr_expiry_dates.reset_index(drop=True, inplace=True)
        
        df_curr_final = pd.DataFrame()
        df_curr_final['expiry'] = df_unique_curr_expiry_dates['expiry'].dt.strftime('%Y-%m-%d')
        df_curr_final['weekly'] = df_unique_curr_expiry_dates['weekly']
        df_curr_final['expiry_type'] = "current"

        with open(curr_expiries_file , 'w') as file:
            file.write(df_curr_final.to_csv(index=False, header=True))
        print(f"{str(datetime.now())} Finished writing Current expiry dates to file {curr_expiries_file}")

        # Merge expired and current expiry dates
        df_merged = pd.concat([df_exp, df_curr_final], ignore_index=True)

        with open(expiries_file , 'w') as file:
            file.write(df_merged.to_csv(index=False, header=True))
        print(f"{str(datetime.now())} Finished writing Expired and Current merged expiry dates to file {expiries_file}")
