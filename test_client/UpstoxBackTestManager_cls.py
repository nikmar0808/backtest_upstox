import sys, os
from backtest_common import __backtestconfig__
from backtest_common.StrategyConfig_cls import StrategyConfig
from backtest_common.ReportGenerator_cls import ReportGenerator
from upstox_core.data_creators.ScripMasterAPIs_cls import ScripMasterAPIs
from upstox_core.data_creators.HistoryDataCreator_cls import HistoryDataCreator
from upstox_core.data_creators.SignalDataCreator_cls import SignalDataCreator
from upstox_core.data_creators.TradeDataCreator_cls import TradeDataCreator

def main():

    """
    """

    history_data_creator = HistoryDataCreator(broker="UPSTOX")

    # Get Nifty historical candle data
    interval = "1"
    unit = "minutes"
    instrument_key = "NSE_INDEX|Nifty 50"
    file_name = f"Nifty_HistoryData_{interval}m.csv"
    history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, file_name)
    history_data_creator.write_historical_data_to_raw_file(instrument_key, interval, unit)

    interval = "3"
    unit = "minutes"
    instrument_key = "NSE_INDEX|Nifty 50"
    file_name = f"Nifty_HistoryData_{interval}m.csv"
    history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, file_name)
    history_data_creator.write_historical_data_to_raw_file(instrument_key, interval, unit)

    interval = "5"
    unit = "minutes"
    instrument_key = "NSE_INDEX|Nifty 50"
    file_name = f"Nifty_HistoryData_{interval}m.csv"
    history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, file_name)
    history_data_creator.write_historical_data_to_raw_file(instrument_key, interval, unit)

    interval = "15"
    unit = "minutes"
    instrument_key = "NSE_INDEX|Nifty 50"
    file_name = f"Nifty_HistoryData_{interval}m.csv"
    history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, file_name)
    history_data_creator.write_historical_data_to_raw_file(instrument_key, interval, unit)

    interval = "30"
    unit = "minutes"
    instrument_key = "NSE_INDEX|Nifty 50"
    file_name = f"Nifty_HistoryData_{interval}m.csv"
    history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, file_name)
    history_data_creator.write_historical_data_to_raw_file(instrument_key, interval, unit)

    interval = "1"
    unit = "days"
    instrument_key = "NSE_INDEX|Nifty 50"
    file_name = f"Nifty_HistoryData_daily.csv"
    history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, file_name)
    history_data_creator.write_historical_data_to_raw_file(instrument_key, interval, unit)

    interval = "1"
    unit = "weeks"
    instrument_key = "NSE_INDEX|Nifty 50"
    file_name = f"Nifty_HistoryData_weekly.csv"
    history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, file_name)
    history_data_creator.write_historical_data_to_raw_file(instrument_key, interval, unit)

    # Get BankNifty historical candle data
    interval = "1"
    unit = "minutes"
    instrument_key = "NSE_INDEX|Nifty Bank"
    file_name = f"Nifty_HistoryData_{interval}m.csv"
    history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, file_name)
    history_data_creator.write_historical_data_to_raw_file(instrument_key, interval, unit)

    interval = "3"
    unit = "minutes"
    instrument_key = "NSE_INDEX|Nifty Bank"
    file_name = f"Nifty_HistoryData_{interval}m.csv"
    history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, file_name)
    history_data_creator.write_historical_data_to_raw_file(instrument_key, interval, unit)

    interval = "5"
    unit = "minutes"
    instrument_key = "NSE_INDEX|Nifty Bank"
    file_name = f"Nifty_HistoryData_{interval}m.csv"
    history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, file_name)
    history_data_creator.write_historical_data_to_raw_file(instrument_key, interval, unit)

    interval = "15"
    unit = "minutes"
    instrument_key = "NSE_INDEX|Nifty Bank"
    file_name = f"Nifty_HistoryData_{interval}m.csv"
    history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, file_name)
    history_data_creator.write_historical_data_to_raw_file(instrument_key, interval, unit)

    interval = "30"
    unit = "minutes"
    instrument_key = "NSE_INDEX|Nifty Bank"
    file_name = f"Nifty_HistoryData_{interval}m.csv"
    history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, file_name)
    history_data_creator.write_historical_data_to_raw_file(instrument_key, interval, unit)

    interval = "1"
    unit = "days"
    instrument_key = "NSE_INDEX|Nifty Bank"
    file_name = f"BankNifty_HistoryData_daily.csv"
    history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, file_name)
    history_data_creator.write_historical_data_to_raw_file(instrument_key, interval, unit)

    interval = "1"
    unit = "weeks"
    instrument_key = "NSE_INDEX|Nifty Bank"
    file_name = f"BankNifty_HistoryData_weekly.csv"
    history_data_raw_file = os.path.join(__backtestconfig__.HISTORY_DATA_RAW_FILE_DIR, file_name)
    history_data_creator.write_historical_data_to_raw_file(instrument_key, interval, unit)

    # These calls get expired contracts for Nifty
    instrument_key = "NSE_INDEX|Nifty 50"
    expiry_dates = history_data_creator.get_expired_expiries(instrument_key)
    get_expired_option_contracts = history_data_creator.get_expired_option_contracts(instrument_key, expiry_dates)

    # These calls get expired contracts for BankNifty
    instrument_key = "NSE_INDEX|Nifty Bank"
    expiry_dates = history_data_creator.get_expired_expiries(instrument_key)
    get_expired_option_contracts = history_data_creator.get_expired_option_contracts(instrument_key, expiry_dates)
    
    scpmaster_utils_obj = ScripMasterAPIs(broker="UPSTOX")
    # This call gets only currently active contracts
    scpmaster_utils_obj.get_scrip_master()

    # Get all expiry dates for Nifty
    instrument_key = "NSE_INDEX|Nifty 50"
    scpmaster_utils_obj.merge_exp_curr_expiry_dates(instrument_key)

    # Get all expiry dates for BankNifty
    instrument_key = "NSE_INDEX|Nifty Bank"
    scpmaster_utils_obj.merge_exp_curr_expiry_dates(instrument_key)

    strategy_config = StrategyConfig(broker="UPSTOX")
    strategies = strategy_config.configure_strategies()

    signal_data_creator = SignalDataCreator(broker="UPSTOX")
    trade_data_creator = TradeDataCreator(broker="UPSTOX")

    report_generator = ReportGenerator(broker="UPSTOX")

    for strategy_obj in strategies:

        signal_data_creator.create_signal_data_for_strategy(strategy_obj)

        trade_data_creator.create_trade_data_for_strategy(strategy_obj)

        report_generator.generate_signal_level_reports(strategy_obj.strategy_id)

    report_generator.generate_aggregate_pnl_reports()
    
    drawdown_on_profitable_trades = report_generator.calc_unrealized_final_pnl_left_on_table()
    for res in drawdown_on_profitable_trades.itertuples():
        print(f"{res}")

    print(f"{report_generator.calc_optimal_thresholds()}")

if __name__ == '__main__':
    main()
