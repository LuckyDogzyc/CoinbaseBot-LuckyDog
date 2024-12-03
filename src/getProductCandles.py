import time
from restClient import client
from datetime import timedelta
from timeStamps import generate_unix_timestamp

# product = client.get_product(product_id = 'XRP-USD')
# print("Product info: ")
# print(product)

def get_candles(minutes=0, hours=0, days=0, seconds=0):
    endTime = generate_unix_timestamp(minutes, hours, days, seconds)
    start_time = generate_unix_timestamp(minutes + 250, hours, days, seconds)
    return client.get_candles(product_id = 'XRP-USD', start = start_time, end = endTime, granularity = "ONE_MINUTE")

candles = get_candles()
# print(candles)
# print(client.get_unix_time().epoch_seconds)
# print(generate_unix_timestamp())


