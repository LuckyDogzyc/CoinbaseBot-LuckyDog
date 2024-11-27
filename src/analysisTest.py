from datetime import datetime, timedelta
from analysis import analysis
from timeStamps import convert_timedelta_to_seconds
import time

def analysis_test(start_time_str, end_time_str, interval_minutes=5, tps=3):
    """
    从指定的开始时间到结束时间，每隔 interval_minutes 分钟运行一次 analysis 函数。
    以指定的 TPS（每秒处理次数）运行，默认为 3 TPS。
    """
    # 将字符串转换为 datetime 对象
    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
    end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')

    # 计算每一步的时间间隔（秒）
    time_per_step = 1.0 / tps  # 每秒处理 tps 次
    t = start_time

    while t <= end_time:
        current_time = datetime.utcnow()
        # print(f"\n运行时间：{current_time}")

        # 计算从开始时间到当前时间的秒数，作为 analysis 函数的参数
        seconds_difference = convert_timedelta_to_seconds(current_time - t)

        # 调用 analysis 函数，传递 seconds_difference 参数
        analysis(seconds=seconds_difference)

        # 时间步进
        t += timedelta(minutes=interval_minutes)

        # 控制 TPS
        time.sleep(time_per_step)

def main():
    # 设置开始和结束时间，格式为 'YYYY-MM-DD HH:MM:SS'
    start_time_str = '2024-11-27 00:20:00'
    end_time_str = '2024-11-27 01:10:00'

    # 调用 analysis_test 函数，设置 TPS 为 3
    analysis_test(start_time_str, end_time_str, tps=3)

if __name__ == "__main__":
    main()
