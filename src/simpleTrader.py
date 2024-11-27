import logging
import time
import uuid
from analysis import analysis
from datetime import datetime
from restClient import client

CRYPTO = "XRP"
CASH = "USD"
PRODUCT_ID = "XRP-USD"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def get_balances():
    try:
        # Fetch account balances using the SDK
        response = client.get_accounts()

        # Extract the list of accounts from the response
        accounts = response['accounts']

        # Log the raw accounts response for debugging
        #logger.debug(f"Accounts data: {accounts}")

        crypto_balance = None
        cash_balance = None

        # Loop through the accounts to find balances for BTC and USDC
        for account in accounts:
            currency = account['currency']
            available_balance = account['available_balance']['value']

            if currency == CRYPTO:
                crypto_balance = float(available_balance)
            elif currency == CASH:
                cash_balance = float(available_balance)

        # Print and return balances
        if crypto_balance is not None:
            print(f"Your {CRYPTO} balance is: {crypto_balance}")
        else:
            print(f"{CRYPTO} account not found.")

        if cash_balance is not None:
            print(f"Your {CASH} balance is: ${cash_balance}")
        else:
            print(f"{CASH} account not found.")

        return crypto_balance, cash_balance

    except Exception as e:
        logger.exception("Failed to retrieve account balances.")
        return None, None

# Get current crypto price
def get_current_crypto_price():
    try:
        logger.info(f"Fetching current {CRYPTO} price...")

        # Fetch the product book data using the SDK's method
        product_book_data = client.get_product_book(product_id=PRODUCT_ID)

        # Extract bids and asks from 'pricebook'
        pricebook = product_book_data['pricebook']
        bids = pricebook['bids']
        asks = pricebook['asks']

        # Get the best bid and ask from the first entry
        best_bid = float(bids[0]['price']) if bids else None
        best_ask = float(asks[0]['price']) if asks else None

        # Calculate the midpoint as the current price
        if best_bid and best_ask:
            current_price = (best_bid + best_ask) / 2
            logger.info(f"Calculated {CRYPTO} price: {current_price:.8f} {CASH} (midpoint of best_bid and best_ask)")
            return current_price
        else:
            logger.error("Best bid or best ask is missing.")
            return None

    except Exception as e:
        logger.exception(f"Failed to retrieve {CRYPTO} price.")
        return None


# Place buy order for 30% of the total cash
def percentage_market_order_buy(price, cash_amount):
    try:
        buy_amount = cash_amount * 0.3
        logger.info(f"Placing buy order for {buy_amount:.2f} {CASH} at {price:.2f} {CASH}/{CRYPTO}")

        # Generate a unique order ID
        order_id = str(uuid.uuid4())

        # Use the SDK's built-in method to place a buy order
        order = client.market_order_buy(
            product_id=PRODUCT_ID, 
            quote_size=f"{buy_amount:.2f}",  # The amount of USDC to spend
            client_order_id=order_id
        )

        logger.info(f"Buy order placed successfully at price {price:.2f} {CASH}/{CRYPTO}")
    except Exception as e:
        logger.exception("Error placing buy order.")



# Place sell order for 60% of the total crypto
def percentage_market_order_sell(price, crypto_amount):
    try:
        sell_amount = crypto_amount * 0.6
        logger.info(f"Placing sell order for {sell_amount:.8f} {CRYPTO} at {price:.2f} {CASH}/{CRYPTO}")

        # Generate a unique order ID
        order_id = str(uuid.uuid4())

        # Use the SDK's built-in method to place a sell order
        order = client.market_order_sell(
            product_id=PRODUCT_ID, 
            base_size=f"{sell_amount:.8f}",  # The amount of crypto to sell
            client_order_id=order_id
        )

        logger.info(f"Sell order placed successfully at price {price:.2f} {CASH}/{CRYPTO}")
    except Exception as e:
        logger.exception("Error placing sell order.")



# Main trading logic
def main():
    logger.info("Starting main trading loop...")
    while True:
        # Get the current balances
        crypto_amount, cash_amount = get_balances()

        if crypto_amount is None or cash_amount is None:
            logger.warning("Failed to retrieve account balances. Skipping this cycle.")
            continue

        # # Fetch real-time market data and construct prompt for LLM
        # best_bid, best_ask = get_product_book(PRODUCT_ID)
        # print(best_bid, best_ask)

        # Add RSI and Bollinger Bands value to prompt
        rsi, percent_b = analysis()

        current_price = get_current_crypto_price()

        if percent_b > 0.94:
            print("BUY NOW!")
            percentage_market_order_buy(current_price, cash_amount)
        elif percent_b < 0.06:
            print("SELL NOW!")
            percentage_market_order_sell(current_price, crypto_amount)
        else:
            print("HOLD")

        # sleep for 5 minutes
        time.sleep(300)

if __name__ == "__main__":
    main()


