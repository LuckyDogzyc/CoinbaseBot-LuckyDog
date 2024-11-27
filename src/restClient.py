from coinbase.rest import RESTClient
from accountConfigs import key_file

# Debug
# client = RESTClient(key_file=key_file, verbose=True, rate_limit_headers=True)

client = RESTClient(key_file=key_file, rate_limit_headers=True)