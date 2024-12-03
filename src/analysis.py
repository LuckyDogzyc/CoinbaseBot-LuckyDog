from technicalAnalysis import process_candle_data, calculate_indicators, detect_golden_death_cross
from getProductCandles import get_candles

def analysis(minutes=0, hours=0, days=0, seconds=0):
    # 处理蜡烛数据
    df = process_candle_data(get_candles(minutes, hours, days, seconds))
    # 计算指标
    df = calculate_indicators(df)
    # 检测金叉和死叉
    df = detect_golden_death_cross(df)

    # 获取最新一条数据
    latest_data = df.iloc[-1]
    # print(latest_data)

    # # 判断当前走势
    signal = latest_data['signal']
    # if latest_data['signal'] == 1:
    #     print("出现金叉信号，可能是买入机会。")
    # elif latest_data['signal'] == -1:
    #     print("出现死叉信号，可能是卖出信号。")

    # # 判断RSI超买超卖
    rsi = latest_data['RSI']
    # if rsi > 70:
    #     print("RSI进入超买区域，注意价格可能回调。")
    # elif rsi < 30:
    #     print("RSI进入超卖区域，注意价格可能反弹。")

    # # 判断布林带位置
    percent_b = latest_data['PercentB']
    # if percent_b > 1:
    #     print("价格高于布林带上轨，可能超买。")
    # elif percent_b < 0:
    #     print("价格低于布林带下轨，可能超卖。")

    print(f"TimeFrame: {latest_data['start']}, signal: {signal}, RSI value: {rsi:.2f}, Bollinger Bands% value: {percent_b:.2f}. ")
    # print(f"Low: {latest_data['low']}, High: {latest_data['high']}, Open: {latest_data['open']}, Close: {latest_data['close']}")
    return signal, rsi, percent_b

def main():
    analysis()

if __name__ == "__main__":
    main()