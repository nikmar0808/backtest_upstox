from __future__ import print_function
import upstox_client
from backtest_common import __backtestconfig__
import logging

# Create and configure logger
general_data_handler_logger = logging.getLogger("logs/market_data_handler_logger.log")
general_data_handler_logger.addHandler(logging.FileHandler("logs/general_data_handler_logger.log", mode='a'))

class GeneralDataAPIs:

    def __init__(self,api_key=None,access_Token=None,debug=True,logger=general_data_handler_logger): 
        self.debug=debug
        self.logger=logger
        self.file_path_master = __backtestconfig__.instrument_script_master_json_file
        self.file_path_fut = __backtestconfig__.instrument_script_master_nfo_index_fut_file
        self.file_path_opt = __backtestconfig__.instrument_script_master_nfo_index_opt_file


    def login_and_authorize(self, api_version, configuration, client_id, client_secret, redirect_uri, auth_code):
        # Login API
        api_instance = upstox_client.LoginApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.token(api_version, code=auth_code, client_id=client_id,
                                        client_secret=client_secret, redirect_uri=redirect_uri, grant_type="authorization_code")
        return api_response.access_token


    def get_profile(self, api_version, configuration):
        api_instance = upstox_client.UserApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_profile(api_version)
        return api_response


    def get_funds_and_margin(self, api_version, configuration):
        api_instance = upstox_client.UserApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_user_fund_margin(api_version)
        return api_response


    def get_positions(self, api_version, configuration):
        api_instance = upstox_client.PortfolioApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_positions(api_version)
        return api_response

    
    def get_holdings(self, api_version, configuration):
        api_instance = upstox_client.PortfolioApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_holdings(api_version)
        return api_response


    def get_trade_history(self, api_version, configuration):
        api_instance = upstox_client.OrderApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_trade_history(api_version)
        return api_response


    def get_trade_wise_profit_and_loss_meta_data(self, api_version, configuration, segment, year):
        api_instance = upstox_client.TradeProfitAndLossApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_trade_wise_profit_and_loss_meta_data(
            segment, year, api_version)
        return api_response

    def get_trade_wise_profit_and_loss_data(self, api_version, configuration, segment, year):
        api_instance = upstox_client.TradeProfitAndLossApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_trade_wise_profit_and_loss_data(
            segment, year, 1, 3000, api_version)
        return api_response


    def get_profit_and_loss_charges(self, api_version, configuration, segment, year):
        api_instance = upstox_client.TradeProfitAndLossApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_profit_and_loss_charges(
            segment, year, api_version)
        return api_response


    def get_brokerage(self, api_version, configuration, instrument_key, quantity, product, transaction_type, price):
        api_instance = upstox_client.ChargeApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_brokerage(
            instrument_key, quantity, product, transaction_type, price, api_version)
        return api_response
