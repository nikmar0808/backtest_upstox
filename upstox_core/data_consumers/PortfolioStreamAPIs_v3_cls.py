import upstox_client
from upstox_core import __upstoxconfig__
import logging

# Create and configure logger
portfolio_stream_apis_logger = logging.getLogger("portfolio_stream_apis.log")
portfolio_stream_apis_logger.addHandler(logging.FileHandler("portfolio_stream_apis.log", mode='a'))

class PortfolioStreamAPIs_v3:

    def __init__(self,api_key=None,access_Token=None,debug=True,logger=portfolio_stream_apis_logger): 
        self.debug=debug
        self.logger=logger
        self.file_path_master = __upstoxconfig__.instrument_script_master_json_file
        self.file_path_fut = __upstoxconfig__.instrument_script_master_nfo_index_fut_file
        self.file_path_opt = __upstoxconfig__.instrument_script_master_nfo_index_opt_file


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


    def place_order(self, api_version, configuration, order_details):
        api_instance = upstox_client.OrderApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.place_order(order_details, api_version)
        return api_response


    def modify_order(self, api_version, configuration, order_details):
        api_instance = upstox_client.OrderApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.modify_order(order_details, api_version)
        return api_response


    def cancel_order(self, api_version, configuration, order_id):
        api_instance = upstox_client.OrderApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.cancel_order(order_id, api_version)
        return api_response


    def get_trades_by_order(self, api_version, configuration, order_id):
        api_instance = upstox_client.OrderApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_trades_by_order(order_id, api_version)
        return api_response


    def get_trade_history(self, api_version, configuration):
        api_instance = upstox_client.OrderApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_trade_history(api_version)
        return api_response


    def get_order_book(self, api_version, configuration):
        api_instance = upstox_client.OrderApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_order_book(api_version)
        return api_response


    def get_order_details(self, api_version, configuration, order_id):
        api_instance = upstox_client.OrderApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_order_details(
            api_version, order_id=order_id)
        return api_response


    def convert_positions(self, api_version, configuration, body):
        api_instance = upstox_client.PortfolioApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.convert_positions(body, api_version)
        return api_response

    # V2
    def get_full_market_quote(self, api_version, configuration, instrument_key):
        api_instance = upstox_client.MarketQuoteApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_full_market_quote(
            instrument_key, api_version)
        return api_response

    # V3
    def get_market_quote_ohlc(self, configuration, interval, instrument_key):
        api_instance = upstox_client.MarketQuoteV3Api(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_market_quote_ohlc(
            interval, instrument_key=instrument_key, async_req=False)
        return api_response

    # V3
    def get_ltp(self, configuration, instrument_key):
        api_instance = upstox_client.MarketQuoteV3Api(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_ltp(
            instrument_key=instrument_key, async_req=False)
        return api_response

    # Without From Date V3
    def get_historical_candle_data(self, configuration, instrument_key, unit, interval, to_date, from_date=None):
        api_instance = upstox_client.HistoryV3Api(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_historical_candle_data(
            instrument_key=instrument_key, unit=unit, interval=interval, to_date=to_date, async_req=False)
        return api_response
    
    # With From Date V3
    def get_historical_candle_data1(self, configuration, instrument_key, unit, interval, to_date, from_date):
        api_instance = upstox_client.HistoryV3Api(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_historical_candle_data1(
            instrument_key=instrument_key, unit=unit, interval=interval, to_date=to_date, from_date=from_date, async_req=False)
        return api_response

    def get_intra_day_candle_data(self, configuration, instrument_key, unit, interval):
        api_instance = upstox_client.HistoryV3Api(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_intra_day_candle_data(
            instrument_key=instrument_key, unit=unit, interval=interval)
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


