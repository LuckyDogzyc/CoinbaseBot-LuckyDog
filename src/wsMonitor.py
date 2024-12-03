import os
import websocket
import json
import threading
import time
from datetime import datetime, timedelta
from discordNotification import send_discord_notification

# 存储交易数据的全局变量
trade_data = []
VOLUME_THRESHOLD = 1400000
PRODUCT_IDS = ["XRP-USD"]  # 替换为您感兴趣的交易对

# 定义时间窗口（例如，最近1分钟）
WINDOW_DURATION = timedelta(minutes=1)

def on_message(ws, message):
    data = json.loads(message)
    if data['type'] == 'match':
        trade = {
            'time': datetime.strptime(data['time'], '%Y-%m-%dT%H:%M:%S.%fZ'),
            'price': float(data['price']),
            'size': float(data['size']),
            'side': data['side'],  # 'buy' or 'sell'
            'product_id': data['product_id']
        }
        trade_data.append(trade)

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws):
    print("WebSocket connection closed")

def on_open(ws):
    print("WebSocket connection opened")
    subscribe_message = {
        "type": "subscribe",
        "channels": [
            {
                "name": "matches",
                "product_ids": PRODUCT_IDS
            }
        ]
    }
    ws.send(json.dumps(subscribe_message))

def start_websocket():
    ws = websocket.WebSocketApp(
        "wss://ws-feed.exchange.coinbase.com",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

def process_trade_data():
    while True:
        # 等待一定时间间隔（例如，每10秒处理一次数据）
        time.sleep(30)

        # 获取当前时间
        now = datetime.utcnow()
        window_start = now - WINDOW_DURATION

        # 过滤时间窗口内的交易数据
        window_trades = [trade for trade in trade_data if trade['time'] >= window_start]

        # 计算买入和卖出总量
        buy_volume = sum(trade['size'] for trade in window_trades if trade['side'] == 'buy')
        sell_volume = sum(trade['size'] for trade in window_trades if trade['side'] == 'sell')
        total_volume = buy_volume + sell_volume
        ratio = calculate_ratio(buy_volume, sell_volume)

        result = f"\nTime Window：{window_start.strftime('%Y-%m-%d %H:%M:%S')} - {now.strftime('%Y-%m-%d %H:%M:%S')}, Buy Volume: {buy_volume}, Sell Volume: {sell_volume}, Ratio: {ratio}, Total Volume: {total_volume} "

        print(result)

        write_to_file(result)

        # Send notification to discord if reach specific condition
        if total_volume >= VOLUME_THRESHOLD:
            send_discord_notification(result)

        # 清理过期的交易数据，防止列表无限增长
        trade_data[:] = [trade for trade in trade_data if trade['time'] >= window_start]

def write_to_file(input, max_lines=1000):
    file_path = 'trade_analysis.txt'
    try:
        # 读取现有的文件内容
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []

        # 添加新数据
        lines.append(input)

        # 如果行数超过最大值，删除最旧的行
        if len(lines) > max_lines:
            lines = lines[-max_lines:]

        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    except Exception as e:
        raise Exception(f"写入文件时发生错误：{e}")


def calculate_ratio(buy_volume, sell_volume):
    if buy_volume > sell_volume:
        return ((buy_volume - sell_volume) / sell_volume) * 100
    elif sell_volume > buy_volume:
        return -((sell_volume - buy_volume) / buy_volume) * 100
    else:
        return 0.0

if __name__ == "__main__":
    # 启动WebSocket连接的线程
    websocket_thread = threading.Thread(target=start_websocket)
    websocket_thread.daemon = True
    websocket_thread.start()

    # 启动处理交易数据的线程
    process_thread = threading.Thread(target=process_trade_data)
    process_thread.daemon = True
    process_thread.start()

    # 主线程保持运行
    while True:
        time.sleep(1)