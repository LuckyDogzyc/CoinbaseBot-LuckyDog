import pandas as pd
import numpy as np
from getProductCandles import get_candles

def detect_golden_death_cross(df):
    """
    检测金叉和死叉信号。
    :param df: 包含MA5和MA10的DataFrame
    :return: DataFrame，新增一列'signal'，标记金叉和死叉
    """
    df = df.copy()
    df['signal'] = 0  # 初始化信号列

    # 当短期MA上穿长期MA，标记为1（金叉）
    df.loc[(df['MA5'] > df['MA10']) & (df['MA5'].shift(1) <= df['MA10'].shift(1)), 'signal'] = 1

    # 当短期MA下穿长期MA，标记为-1（死叉）
    df.loc[(df['MA5'] < df['MA10']) & (df['MA5'].shift(1) >= df['MA10'].shift(1)), 'signal'] = -1

    return df

def calculate_bollinger_percent_b(df):
    """
    计算布林带百分比（%B）。
    :param df: 包含收盘价和布林带的DataFrame
    :return: DataFrame，新增一列'PercentB'
    """
    df = df.copy()
    df['PercentB'] = (df['close'] - df['LowerBand']) / (df['UpperBand'] - df['LowerBand'])
    return df

def calculate_indicators(df):
    # 确保有足够的数据进行计算
    if len(df) < 20:
        raise Exception("ERROR: Need at least 20 datapoints to analyse.")

    # 计算移动平均线（MA）
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA10'] = df['close'].rolling(window=10).mean()

    # 计算布林带（Bollinger Bands）
    df['MiddleBand'] = df['close'].rolling(window=20).mean()
    df['StdDev'] = df['close'].rolling(window=20).std()
    df['UpperBand'] = df['MiddleBand'] + (df['StdDev'] * 2)
    df['LowerBand'] = df['MiddleBand'] - (df['StdDev'] * 2)

    # 计算相对强弱指数（RSI）
    delta = df['close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    average_gain = up.rolling(window=14).mean()
    average_loss = down.rolling(window=14).mean()
    rs = average_gain / average_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df = calculate_bollinger_percent_b(df)

    return df

def process_candle_data(candles):
    data_list = []
    for candle in candles['candles']:
        data = {
            'start': candle.start,
            'low': candle.low,
            'high': candle.high,
            'open': candle.open,
            'close': candle.close,
            'volume': candle.volume
        }
        data_list.append(data)

    # 创建DataFrame
    df = pd.DataFrame(data_list)

    # 数据类型转换
    df['start'] = pd.to_datetime(df['start'].astype(int), unit='s', utc=True)
    numeric_columns = ['open', 'high', 'low', 'close', 'volume']
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)

    return df

def get_latest_indicators(df):
    # 计算指标
    df = calculate_indicators(df)

    # 获取最新一条数据的指标值
    latest_data = df.iloc[-1]
    indicators = {
        'TimeFrame': latest_data['start'],
        'close_price': latest_data['close'],
        'MA5': latest_data.get('MA5', np.nan),
        'MA10': latest_data.get('MA10', np.nan),
        'UpperBand': latest_data.get('UpperBand', np.nan),
        'MiddleBand': latest_data.get('MiddleBand', np.nan),
        'LowerBand': latest_data.get('LowerBand', np.nan),
        'RSI': latest_data.get('RSI', np.nan)
    }

    return indicators

def main():
    # 处理蜡烛数据
    df = process_candle_data(get_candles())
    # 计算指标
    df = calculate_indicators(df)
    # 检测金叉和死叉
    df = detect_golden_death_cross(df)
    # 获取最新的指标和信号
    latest_data = df.iloc[-1]
    indicators = {
        'TimeFrame': latest_data['start'],
        'close_price': latest_data['close'],
        'MA5': latest_data.get('MA5', np.nan),
        'MA10': latest_data.get('MA10', np.nan),
        'UpperBand': latest_data.get('UpperBand', np.nan),
        'MiddleBand': latest_data.get('MiddleBand', np.nan),
        'LowerBand': latest_data.get('LowerBand', np.nan),
        'RSI': latest_data.get('RSI', np.nan),
        'Signal': latest_data.get('signal', 0)  # 获取最新的交易信号
    }

    # 打印指标信息和交易信号
    log_message = (
        f"TimeFrame: {indicators['TimeFrame']}, "
        f"最新收盘价: {indicators['close_price']:.4f}, MA5: {indicators['MA5']:.4f}, MA10: {indicators['MA10']:.4f}, "
        f"上轨: {indicators['UpperBand']:.4f}, 中轨: {indicators['MiddleBand']:.4f}, 下轨: {indicators['LowerBand']:.4f}, "
        f"RSI: {indicators['RSI']:.2f}, Signal: {indicators['Signal']}"
    )

    print(log_message)

if __name__ == "__main__":
    main()
