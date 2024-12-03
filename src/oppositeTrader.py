import logging
import time
import uuid
import os
import re
from datetime import datetime
from restClient import client
from restClientHelper import market_order_buy, market_order_sell

CRYPTO = "XRP"
CASH = "USD"
PRODUCT_ID = "XRP-USD"
WAIT_TIME = 30

# Configure logging
logging.basicConfig(
    level=logging.INFO,
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

        crypto_balance = None
        cash_balance = None

        # Loop through the accounts to find balances for CRYPTO and CASH
        for account in accounts:
            currency = account['currency']
            available_balance = account['available_balance']['value']

            if currency == CRYPTO:
                crypto_balance = float(available_balance)
            elif currency == CASH:
                cash_balance = float(available_balance)

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

def percentage_market_order_buy(price, cash_amount, percentage):
    try:
        spend_cash = cash_amount * (percentage / 100)
        buy_amount = spend_cash / price
        logger.info(f"Placing buy order for {buy_amount:.2f} {CRYPTO} at {price:.4f} {CASH}")
        market_order_buy(PRODUCT_ID, buy_amount)
    except Exception as e:
        logger.exception("Error placing buy order.")

def percentage_market_order_sell(price, crypto_amount, percentage):
    try:
        sell_amount = crypto_amount * (percentage / 100)
        logger.info(f"Placing sell order for {sell_amount:.2f} {CRYPTO} at {price:.4f} {CASH}")
        market_order_sell(PRODUCT_ID, sell_amount)
    except Exception as e:
        logger.exception("Error placing sell order.")

def read_wsmonitor_output():
    try:
        # 定义文件路径
        file_path = 'trade_analysis.txt'

        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.warning(f"{file_path} 文件不存在。")
            return None

        # 读取文件内容，获取所有数据点
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 过滤非空行
        lines = [line.strip() for line in lines if line.strip()]

        if len(lines) < 3:
            logger.warning("数据点不足，无法进行判断。")
            return None

        data_points = []

        # 使用正则表达式解析数据
        for line in lines:
            try:
                total_volume_match = re.search(r'Total Volume: (\d+\.?\d*)', line)
                ratio_match = re.search(r'Ratio: ([+-]?\d+\.?\d*)', line)
                if total_volume_match and ratio_match:
                    total_volume = float(total_volume_match.group(1))
                    ratio = float(ratio_match.group(1))
                    data_points.append({'total_volume': total_volume, 'ratio': ratio})
            except Exception as e:
                logger.exception("解析数据点时出错。")
                continue  # 跳过错误的数据点

        if len(data_points) < 3:
            logger.warning("无法解析足够的数据点。")
            return None

        return data_points

    except Exception as e:
        logger.exception("读取 wsMonitor 输出时出错。")
        return None

def check_trading_conditions(data_points):
    if not data_points or len(data_points) < 3:
        return 'hold', 0  # 返回动作和交易百分比

    # 初始化变量
    streak = 0  # 连续满足条件的数据点数量
    current_sign = None  # 当前 Ratio 的符号

    # 倒序遍历数据点，检查连续性
    for point in reversed(data_points):
        if point['total_volume'] > 1400000:
            ratio = point['ratio']
            if current_sign is None:
                # 第一个数据点，确定符号
                current_sign = 'positive' if ratio > 0 else 'negative'
                streak += 1
            else:
                # 检查符号是否一致
                if (ratio > 0 and current_sign == 'positive') or (ratio < 0 and current_sign == 'negative'):
                    streak += 1
                else:
                    # 符号不一致，停止遍历
                    break
        else:
            # Total Volume 不满足条件，停止遍历
            break

    # 判断交易条件
    if streak >= 3:
        if current_sign == 'positive':
            # 买入条件
            percentage = min(3 + (streak - 3), 50)
            logger.info(f"连续 {streak} 个数据点满足买入条件，买入 {percentage}% 的现金余额。")
            return 'buy', percentage
        elif current_sign == 'negative':
            # 卖出条件
            percentage = min(1 + (streak - 3), 50)
            logger.info(f"连续 {streak} 个数据点满足卖出条件，卖出 {percentage}% 的持仓。")
            return 'sell', percentage
    else:
        return 'hold', 0


def main():
    logger.info("Starting main trading loop...")
    while True:
        # 读取 wsMonitor 的输出
        data_points = read_wsmonitor_output()
        if not data_points:
            logger.info("无法获取有效的数据点，等待下一个周期。")
            time.sleep(WAIT_TIME)  # 等待WAIT_TIME sec
            continue

        # 检查交易条件
        action, percentage = check_trading_conditions(data_points)

        # # 获取当前价格和账户余额
        crypto_amount, cash_amount = get_balances()
        current_price = get_current_crypto_price()

        if not current_price or crypto_amount is None or cash_amount is None:
            logger.warning("无法获取账户余额或当前价格，跳过本次循环。")
            time.sleep(60)
            continue

        # print(crypto_amount, cash_amount, current_price)

        if action == 'sell' and percentage > 0:
            logger.info(f"满足卖出条件，连续满足条件的数据点数量：{percentage + 2}，卖出 {percentage}% 的持仓。")
            percentage_market_order_sell(current_price, crypto_amount, percentage)
        elif action == 'buy' and percentage > 0:
            logger.info(f"满足买入条件，连续满足条件的数据点数量：{percentage}，买入 {percentage}% 的现金余额。")
            percentage_market_order_buy(current_price, cash_amount, percentage)
        else:
            logger.info("未满足交易条件，保持持仓。")

        # 等待下一个周期
        time.sleep(WAIT_TIME)  # 根据需要调整等待时间

if __name__ == "__main__":
    main()