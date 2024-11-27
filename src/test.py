from restClient import client
import uuid

response = client.get_accounts()
accounts = response['accounts']

crypto_balance = None
cash_balance = None

# # Loop through the accounts to find balances for BTC and USDC
# for account in accounts:
#     currency = account['currency']
#     available_balance = account['available_balance']['value']

#     if currency == "XRP":
#         crypto_balance = float(available_balance)
#     elif currency == "USD":
#         cash_balance = float(available_balance)

# product_book_data = client.get_product_book(product_id="XRP-USD", limit=100)
# print(product_book_data)

order_id = str(uuid.uuid4())

# Use the SDK's built-in method to place a sell order
order = client.market_order_sell(
    product_id="XRP-USD", 
    base_size=f"0.001",  # The amount of crypto to sell
    client_order_id=order_id
)