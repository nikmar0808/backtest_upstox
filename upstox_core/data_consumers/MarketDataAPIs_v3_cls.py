import upstox_client
from backtest_common import __backtestconfig__
import logging, asyncio, json, ssl, requests, websockets
from google.protobuf.json_format import MessageToDict
from marketfeed_protobuf_v3 import MarketDataFeedV3_pb2 as pb

# Create and configure logger
market_data_apis_logger = logging.getLogger("logs/market_data_apis_v3.log")
market_data_apis_logger.addHandler(logging.FileHandler("logs/market_data_apis_v3.log", mode='a'))

class MarketDataAPIs_v3:

    def __init__(self,debug=True,logger=market_data_apis_logger): 
        self.debug=debug
        self.logger=logger
        self.configuration = upstox_client.Configuration()
        self.configuration.access_token = __backtestconfig__.access_token


    def get_market_data_feed_authorize(self):
        """Get authorization for market data feed."""
        #access_token = __backtestconfig__.access_token
        market_data_feed_v3_authorize_url=__backtestconfig__.market_data_feed_v3_authorize_url
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.configuration.access_token}'
        }
        print(f"API RESPONE OBJECT: {api_response}")
        url = __backtestconfig__.market_data_feed_v3_authorize_url
        api_response = requests.get(url=url, headers=headers)
        print(f"API RESPONE OBJECT: {api_response}")
        return api_response.json()


    def decode_protobuf(self, buffer):
        """Decode protobuf message."""
        feed_response = pb.FeedResponsev3()
        feed_response.ParseFromString(buffer)
        return feed_response


    async def fetch_market_data_feed(self, instrument_key):
        """Fetch market data using WebSocket and print it."""

        # Create default SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Get market data feed authorization
        market_data_feed_authorize = self.get_market_data_feed_authorize()
        # Connect to the WebSocket with SSL context
        async with websockets.connect(market_data_feed_authorize["data"]["authorized_redirect_uri"], ssl=ssl_context) as websocket:
            print('Connection established')

            await asyncio.sleep(1)  # Wait for 1 second

            # Data to be sent over the WebSocket
            data = {
                "guid": "someguid_v3",#Generate Unique across system
                "method": "sub",
                "data": {
                    "mode": "full",
                    "instrumentKeys": instrument_key
                    #"instrumentKeys": ["NSE_INDEX|Nifty Bank", "NSE_INDEX|Nifty 50"]
                }
            }

            # Convert data to binary and send over WebSocket
            binary_data = json.dumps(data).encode('utf-8')
            await websocket.send(binary_data)

            feed_count = 0
            with open(__backtestconfig__.market_data_v3_text_file, "w") as file_text, open(__backtestconfig__.market_data_v3_json_file, "w") as file_json:
            # Continuously receive and decode data from WebSocket
                while True:
                    feed_count += 1
                    message = await websocket.recv()
                    decoded_data = self.decode_protobuf(message)

                    # Convert the decoded data to a dictionary
                    data_dict = MessageToDict(decoded_data)

                    # Print the dictionary representation
                    print(json.dumps(data_dict))

                    file_text.write(f"{data_dict} \n")
                    file_json.write(f"{json.dumps(data_dict)} \n")
                    
                    if feed_count > 499:
                        break
                print("Finished writing 500 feed data")
