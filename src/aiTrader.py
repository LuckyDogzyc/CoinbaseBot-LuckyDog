# edit from https://github.com/DasJager/coinbase-AI-Trader/blob/main/AI_Trader.py

import logging
import time
from analysis import analysis
from datetime import datetime
from ollamaModel import call_llama_model
from restClient import client
from restClientHelper import market_order_buy, market_order_sell

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
            "If the trend just turns positive and the signal is 1, respond with BUY. "
            "If the trend just turns negative and the signal is -1, respond with SELL. "
            "If the trend is positive and strong, respond with BUY. "
            "If the trend is negative and strong, respond with SELL. "
            "If the trend is unclear or weak, respond with HOLD. "
            "Based on this prediction and your strategy, should we BUY, SELL, or HOLD? "
            "Respond with one word: BUY, SELL, or HOLD."
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

# Analyse how many cryptos we should buy
def analysis_buy_price(cash_balance, percent_b):
    buy_percentage = (percent_b + 0.3) * 0.20
    buy_amount = cash_balance * buy_percentage
    print(f"Current {CASH} Balance: {cash_balance}, percent_b: {percent_b}, buy_percentage: {buy_percentage}, buy_amount: {buy_amount}")
    return buy_amount

# Analyse how many cryptos we should sell
def analysis_sell_price(crypto_balance, percent_b):
    sell_percentage = min((1-percent_b) * 0.40, 1)
    sell_amount = crypto_balance * sell_percentage
    print(f"Current {CRYPTO} Balance: {crypto_balance}, percent_b: {percent_b}, sell_percentage: {sell_percentage}, sell_amount: {sell_amount}")
    return sell_amount


# Main trading logic
def main():
    logger.info("Starting main trading loop...")
    while True:
        # Get the current balances
        crypto_balance, cash_balance = get_balances()

        if crypto_balance is None or cash_balance is None:
            logger.warning("Failed to retrieve account balances. Skipping this cycle.")
            continue

        # Fetch real-time market data and construct prompt for LLM
        prompt, best_bid, best_ask = get_product_book(PRODUCT_ID)

        # Add RSI and Bollinger Bands value to prompt
        signal, rsi, percent_b = analysis()
        prompt += (
                f"singal: {signal}, RSI value: {rsi:.2f}, Bollinger Bands% value: {percent_b:.2f}. "
            )

        if prompt and best_bid and best_ask:
            current_price = get_current_crypto_price()
            # Append the current price, balances, and recent trades to the prompt
            prompt += (
                f"Current {CRYPTO} price: {current_price} {CASH}."
                f"{CRYPTO} Balance: {crypto_balance} {CRYPTO}."
                f"{CASH} Balance: {cash_balance} {CASH}."
            )

            print("Prompt: ", prompt)

            # Get the decision from the LLM
            decision = make_llm_trade_decision(prompt)
            logger.info(f"Trade decision: {decision}")

            # Execute the trade based on LLM's decision
            print("decision", decision)
            if decision == "BUY":
                buy_amount = analysis_buy_price(crypto_balance, percent_b)
                market_order_buy(PRODUCT_ID, buy_amount)
                logger.info(f"Buy order placed successfully for {buy_amount:.2f} {CRYPTO}")
            elif decision == "SELL":
                sell_amount = analysis_sell_price(cash_balance, percent_b)
                market_order_sell(PRODUCT_ID, sell_amount)
                logger.info(f"Sell order placed successfully for {sell_amount:.2f} {CRYPTO}")
            else:
                logger.info("Decision was to HOLD, or insufficient balance for trade.")

        else:
            logger.warning("Failed to construct prompt for LLM. Skipping this cycle.")

        # sleep for 1 minutes
        time.sleep(60)

if __name__ == "__main__":
    main()
