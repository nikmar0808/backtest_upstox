import upstox_client
from backtest_common import __backtestconfig__
import logging, asyncio, json, ssl, websockets

# Create and configure logger
pfstream_data_apis_logger = logging.getLogger("logs/pfstream_data_apis.log")
pfstream_data_apis_logger.addHandler(logging.FileHandler("logs/pfstream_data_apis.log", mode='a'))

class PFStreamDataAPIs:

    def __init__(self,debug=True,logger=pfstream_data_apis_logger): 
        self.debug=debug
        self.logger=logger
        self.api_version = "2.0"
        self.configuration = upstox_client.Configuration()
        self.configuration.access_token = __backtestconfig__.access_token

    def get_portfolio_stream_feed_authorize(self):
        api_instance = upstox_client.WebsocketApi(
            upstox_client.ApiClient(self.configuration))
        api_response = api_instance.get_portfolio_stream_feed_authorize(self.api_version,order_update=True,position_update=False,holding_update=False)
        return api_response

    async def fetch_order_updates(self):
        """Fetch Order Updates using WebSocket and print it."""

        # Create default SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Get portfolio stream feed authorization
        portfolio_stream_feed_authorize = self.get_portfolio_stream_feed_authorize()
        # Connect to the WebSocket with SSL context
        async with websockets.connect(portfolio_stream_feed_authorize.data.authorized_redirect_uri, ssl=ssl_context) as websocket:
            print('Connection established')

            await asyncio.sleep(1)  # Wait for 1 second

             # Perform WebSocket operations
            while True:
                message = await websocket.recv()
                print(json.dumps(message))
                #feed_count = 0
                with open(__backtestconfig__.portfolio_sream_feed_text_file, "a") as file_text, open(__backtestconfig__.portfolio_sream_feed_json_file, "a") as file_json:
                    # Continuously receive and decode data from WebSocket
                    """
                    while True:
                    feed_count += 1
                    """
                    message = await websocket.recv()

                    # Print the json representation
                    print(json.dumps(message))

                    file_text.write(f"{message} \n")
                    file_json.write(f"{json.dumps(message)} \n")
                    
                    """
                    if feed_count > 499:
                        break
                    """
                    print("Finished writing Portfolio Stream update received from API")
                

