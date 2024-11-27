# edit from https://github.com/DasJager/coinbase-AI-Trader/blob/main/AI_Trader.py

import logging
import time
import uuid
from analysis import analysis
from datetime import datetime
from ollamaModel import call_llama_model
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

# Function to make a trade decision using LLM and KNN strategy
def make_llm_trade_decision(prompt):
    try:
        # Enhance the prompt with KNN prediction context
        enhanced_prompt = (
            f"{prompt}\n"
            "You are an expert day trader utilizing a KNN prediction model for market analysis. "
            "Recent price movements indicate either an upward or downward trend. "
            "The RSI value indicates the strength of th trend. "
            "If the trend is positive and strong, respond with BUY. "
            "If the trend is negative and strong, respond with SELL. "
            "If the trend is unclear or weak, respond with HOLD. "
            "Based on this prediction and your strategy, should we BUY, SELL, or HOLD? Respond with one word: BUY, SELL, or HOLD."
        )

        logger.debug(f"Sending enhanced prompt to LLM:\n{enhanced_prompt}")
        
        response = call_llama_model(enhanced_prompt)

        logger.debug(f"Raw LLM response: {response}")

        first_line = response.splitlines()[0]

        logger.debug(f"LLM parsed response: {first_line}")

        if "BUY" in first_line:
            return "BUY"
        elif "SELL" in first_line:
            return "SELL"
        elif "HOLD" in first_line:
            return "HOLD"
        else:
            logger.warning("Unclear response from LLM, defaulting to HOLD.")
            return "HOLD"

    except Exception as e:
        logger.exception("Failed to communicate with LLM.")
        return "HOLD"


def get_product_book(product_id):
    try:
        logger.debug(f"Fetching product book data for {product_id}...")

        # Fetch the product book data using the SDK's built-in method
        product_book_data = client.get_product_book(product_id=product_id, limit=100)

        # Log the entire raw response to inspect its structure
        #logger.debug(f"Full product book data: {product_book_data}")

        # Extract bids and asks from the 'pricebook' section of the data
        pricebook = product_book_data['pricebook']
        bids = pricebook['bids']
        asks = pricebook['asks']

        # Find the best bid (highest bid price) and best ask (lowest ask price)
        best_bid = float(bids[0]['price']) if bids else None
        best_ask = float(asks[0]['price']) if asks else None

        if best_bid is None or best_ask is None:
            logger.error("Failed to extract best bid or best ask from the data.")
            return None, None, None

        # recent trades from bids and asks data
        recent_trades = []

        # Assume that each trade happens at the midpoint between a bid and an ask
        for i in range(min(len(bids), len(asks))):
            trade_price = (float(bids[i]['price']) + float(asks[i]['price'])) / 2
            trade_size = min(float(bids[i]['size']), float(asks[i]['size']))  # Assume trade size is the smaller of bid/ask
            recent_trades.append({
                'trade_id': f"trade_{i}",
                'price': trade_price,
                'size': trade_size
            })

        # Log how many trades were simulated
        logger.debug(f"Number of simulated recent trades: {len(recent_trades)}")

        # Condensed format to fit more trades into the prompt
        max_trades = 100  # Set the maximum number of trades to include in the prompt
        recent_trades = recent_trades[:max_trades]

        trades_summary = "".join([
            f"{trade['trade_id']} {trade['price']} {trade['size']}, "
            for trade in recent_trades
        ])

        # Construct a text prompt for the LLM
        prompt = (
            f"Market data for {product_id}: "
            f"Best Bid: {best_bid}, "
            f"Best Ask: {best_ask}, "
            f"Time: {datetime.now()}, "
            f"Recent Trades:{trades_summary}"
        )

        logger.debug(f"Constructed prompt for LLM: {prompt}")

        return prompt, best_bid, best_ask

    except Exception as e:
        logger.exception(f"Error getting product book data for {product_id}: {e}")
        return None, None, None


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


# Place buy order for $2 worth of BTC
def market_order_buy(price):
    try:
        amount_usdc = 2.00  # Trade $2 at a time
        logger.info(f"Placing buy order for {amount_usdc:.2f} USDC at {price:.2f} USDC/BTC")

        # Generate a unique order ID
        order_id = str(uuid.uuid4())

        # Use the SDK's built-in method to place a buy order
        order = client.market_order_buy(
            product_id=PRODUCT_ID, 
            quote_size=f"{amount_usdc:.2f}",  # The amount of USDC to spend
            client_order_id=order_id
        )

        logger.info(f"Buy order placed successfully at price {price:.2f} USDC/BTC")
    except Exception as e:
        logger.exception("Error placing buy order.")



# Place sell order for $2 worth of BTC
def market_order_sell(price):
    try:
        amount_btc = amount_usdc / price  # Convert $2 USDC to BTC at the current price
        logger.info(f"Placing sell order for {amount_btc:.8f} BTC at {price:.2f} USDC/BTC")

        # Generate a unique order ID
        order_id = str(uuid.uuid4())

        # Use the SDK's built-in method to place a sell order
        order = client.market_order_sell(
            product_id=PRODUCT_ID, 
            base_size=f"{amount_btc:.8f}",  # The amount of crypto to sell
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

        # Fetch real-time market data and construct prompt for LLM
        prompt, best_bid, best_ask = get_product_book(PRODUCT_ID)

        # Add RSI and Bollinger Bands value to prompt
        rsi, percent_b = analysis()
        prompt += (
                f"RSI value: {rsi:.2f}, Bollinger Bands% value: {percent_b:.2f}. "
            )

        if prompt and best_bid and best_ask:
            current_price = get_current_crypto_price()
            # Append the current price, balances, and recent trades to the prompt
            prompt += (
                f"Current {CRYPTO} price: {current_price} {CASH}."
                f"{CRYPTO} Balance: {crypto_amount} {CRYPTO}."
                f"{CASH} Balance: {cash_amount} {CASH}."
            )

            print("Prompt: ", prompt)

            # Get the decision from the LLM
            decision = make_llm_trade_decision(prompt)
            logger.info(f"Trade decision: {decision}")

            # Execute the trade based on LLM's decision
            print("decision", decision)
            # if decision == "BUY":
            #     market_order_buy(current_price, cash)
            # elif decision == "SELL":
                # market_order_sell(current_price, crypto)
            # else:
            #     logger.info("Decision was to HOLD, or insufficient balance for trade.")

        else:
            logger.warning("Failed to construct prompt for LLM. Skipping this cycle.")

        # sleep for 5 minutes
        time.sleep(300)

if __name__ == "__main__":
    main()


