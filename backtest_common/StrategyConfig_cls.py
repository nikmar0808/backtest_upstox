import os
from backtest_common import __strategyconfig__
from backtest_common.Strategy_cls import Strategy
from backtest_common.StrategyBase_cls import StrategyBase
from datetime import datetime
import logging
import pandas as pd
import json
import base64
import yaml

# Create and configure logger
strategy_config_logger = logging.getLogger("logs/strategy_config.log")
strategy_config_logger.addHandler(logging.FileHandler("logs/strategy_config.log", mode='a'))
strategy_config_logger.setLevel(logging.INFO)

class StrategyConfig(object):

    def __init__(self, broker, logger=strategy_config_logger):
        self.logger = logger
        self.broker = broker
        self.strategy_file_bin_extn = __strategyconfig__.STRATEGY_FILE_BIN_EXTN
        self.strategy_file_dat_extn = __strategyconfig__.STRATEGY_FILE_DAT_EXTN
        self.strategy_config_file_dir = __strategyconfig__.STRATEGY_CONFIG_DIR
        self.xlsx_file = __strategyconfig__.STRATEGY_CONFIG_EXCEL_FILE

    def configure_strategies(self) -> list[StrategyBase]:
        strategies = []
        for strategy_id in __strategyconfig__.strategies:

            df_from_file = pd.DataFrame()
            strategy_file_dir = self.strategy_config_file_dir
            dat_file_name = f"{strategy_id}{self.strategy_file_dat_extn}"
            strategy_dat_file = os.path.join(strategy_file_dir, dat_file_name)

            if not os.path.isfile(strategy_dat_file):
                self.logger.exception(f"Strategy Config loading exception: File not found {strategy_dat_file}")
                raise FileNotFoundError(f"Strategy Config loading error: File not found {strategy_dat_file}")

            strategy_dtls = {}
            with open(strategy_dat_file, "rt") as cfile:
                strategy_dtls = json.load(cfile)
                print(f"{str(datetime.now())} Loaded Strategy details for {strategy_id} strategy_dtls \n{strategy_dtls}")
            
            if not strategy_dtls:
                self._logger.exception(f"Strategy Config loading exception: Configurations not found for {strategy_id}")
                raise ValueError(f"Strategy Config loading error: Configurations not found for {strategy_id}")

            # Create a Strategy object with the strategy details
            strategy_obj = Strategy(strategy_id, self.broker)
            for key, value in strategy_dtls.items():
                setattr(strategy_obj, key, value)
            print(f"{str(datetime.now())} Configured Strategy details for {strategy_id}")

            strategies.append(strategy_obj)

        return strategies

    def convert_bin_strategies_to_csv(self):

        for strategy_id in __strategyconfig__.strategies:
            print(f"{strategy_id}")
            df_from_file = pd.DataFrame()
            strategy_file_dir = self.strategy_config_file_dir
            bin_file_name = f"{strategy_id}{self.strategy_file_bin_extn}"
            csv_file_name = f"{strategy_id}{self.strategy_file_dat_extn}"
            strategy_bin_file = os.path.join(strategy_file_dir, bin_file_name)
            strategy_csv_file = os.path.join(strategy_file_dir, csv_file_name)
            output_excel_path = os.path.join(strategy_file_dir, self.xlsx_file)

            if not os.path.isfile(strategy_bin_file):
                self.logger.exception(f"config loading exception: File not found {strategy_bin_file}")
                raise FileNotFoundError(f"config loading error: File not found {strategy_bin_file}")

            strategy_dtls = {}
            with open(strategy_bin_file, "rb") as bfile:
                bin_data = bfile.read()
                data = base64.b64decode(bin_data)
                strategy_dtls = yaml.safe_load(data.decode("utf-8"))
            
            if not strategy_dtls:
                self._logger.exception(f"config loading exception: Configurations not found for {strategy_id}")
                raise ValueError(f"config loading error: Configurations not found for {strategy_id}")
            print(f"{str(datetime.now())} {strategy_id} strategy_dtls \n {strategy_dtls}")
            df_from_file = pd.DataFrame.from_dict(strategy_dtls, orient='index')
            #df_from_file = pd.DataFrame(strategy_dtls)

            with open(strategy_csv_file, 'w') as cfile:
                #cfile.write(df_from_file.to_csv(index=True, sep='=', header=False))
                cfile.write(df_from_file.to_csv(index=True, header=False))

            if not df_from_file.empty:
                df_from_file = None
        """
        try:
            with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
                for csv_file_name in os.listdir(strategy_file_dir):
                    if csv_file_name.endswith('.csv'):
                        df = pd.read_csv(os.path.join(strategy_file_dir, csv_file_name))
                        sheet_name = os.path.splitext(csv_file_name)[0]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"CSV files successfully combined into '{output_excel_path}' with separate sheets.")
        except FileNotFoundError:
            print(f"Error: The specified CSV folder path '{strategy_file_dir}' does not exist.")
        except Exception as e:
            print(f"An error occurred: {e}")
        """        

        return

    def convert_csv_strategies_to_bin(self):

        for strategy_id in __strategyconfig__.strategies:
            print(f"{strategy_id}")
            df_from_file = pd.DataFrame()
            strategy_file_dir = self.strategy_config_file_dir
            bin_file_name = f"{strategy_id}{self.strategy_file_bin_extn}"
            csv_file_name = f"{strategy_id}{self.strategy_file_dat_extn}"
            strategy_bin_file = os.path.join(strategy_file_dir, bin_file_name)

            if not os.path.isfile(strategy_bin_file):
                self.logger.exception(f"config loading exception: File not found {strategy_bin_file}")
                raise FileNotFoundError(f"config loading error: File not found {strategy_bin_file}")

            strategy_dtls = {}
            with open(strategy_bin_file, "rb") as bfile:
                bin_data = bfile.read()
                data = base64.b64decode(bin_data)
                strategy_dtls = yaml.safe_load(data.decode("utf-8"))
            
            if not strategy_dtls:
                self._logger.exception(f"config loading exception: Configurations not found for {strategy_id}")
                raise ValueError(f"config loading error: Configurations not found for {strategy_id}")
            print(f"{str(datetime.now())} {strategy_id} strategy_dtls \n {strategy_dtls}")

        return
