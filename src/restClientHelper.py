import uuid
from restClient import client

# Place buy order at certain amount
def market_order_buy(product_id, buy_amount):
    try:
        # Generate a unique order ID
        order_id = str(uuid.uuid4())

        # Use the SDK's built-in method to place a buy order
        order = client.market_order_buy(
            product_id=product_id, 
            quote_size=f"{buy_amount:.2f}",  # The amount of USDC to spend
            client_order_id=order_id
        )
    except Exception as e:
        print("Error placing buy order.")



# Place sell order at certain amount
def market_order_sell(product_id, sell_amount):
    try:
        # Generate a unique order ID
        order_id = str(uuid.uuid4())

        # Use the SDK's built-in method to place a sell order
        order = client.market_order_sell(
            product_id=product_id, 
            base_size=f"{sell_amount:.2f}",  # The amount of crypto to sell
            client_order_id=order_id
        )
    except Exception as e:
        print("Error placing sell order.")