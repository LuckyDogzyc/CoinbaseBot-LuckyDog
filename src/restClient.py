from coinbase.rest import RESTClient
from accountConfigs import key_file

client = RESTClient(key_file=key_file, verbose=True, rate_limit_headers=True)