from __future__ import print_function
import upstox_client
import logging

# Create and configure logger
historydata_apis_logger = logging.getLogger("logs/historydata_apis.log")
historydata_apis_logger.addHandler(logging.FileHandler("logs/historydata_apis.log", mode='a'))

class HistoryDataAPIs:

    def __init__(self,api_key=None,access_Token=None,debug=True,logger=historydata_apis_logger): 
        self.debug=debug
        self.logger=logger

    def login_and_authorize(self, api_version, configuration, client_id, client_secret, redirect_uri, auth_code):
        # Login API
        api_instance = upstox_client.LoginApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.token(api_version, code=auth_code, client_id=client_id,
                                        client_secret=client_secret, redirect_uri=redirect_uri, grant_type="authorization_code")
        return api_response.access_token

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

    # V3
    def get_intra_day_candle_data(self, configuration, instrument_key, unit, interval):
        api_instance = upstox_client.HistoryV3Api(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_intra_day_candle_data(
            instrument_key=instrument_key, unit=unit, interval=interval)
        return api_response

    # V3
    def get_expired_historical_data(self, configuration, expired_instrument_key, interval, to_date, from_date):
        api_instance = upstox_client.ExpiredInstrumentApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_expired_historical_candle_data(
            expired_instrument_key=expired_instrument_key, interval=interval, to_date=to_date, from_date=from_date, async_req=False)
        return api_response

    # Plus
    def get_expired_option_contracts(self, configuration, expired_instrument_key, expiry_date):
        api_instance = upstox_client.ExpiredInstrumentApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_expired_option_contracts(
            instrument_key=expired_instrument_key, expiry_date=expiry_date)
        return api_response

    def get_expiries(self, configuration, underlying_instrument_key):
        api_instance = upstox_client.ExpiredInstrumentApi(
            upstox_client.ApiClient(configuration))
        api_response = response = api_instance.get_expiries(instrument_key=underlying_instrument_key)
        return api_response
