import time
from restClient import client
from datetime import datetime, timedelta

def dhms_to_seconds(hours, minutes, seconds):
    return (hours * 60 + minutes) * 60 + seconds

def convert_timedelta(duration):
    days, seconds = duration.days, duration.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return hours, minutes, seconds

def convert_timedelta_to_seconds(duration):
    hours, minutes, seconds = convert_timedelta(duration)
    return dhms_to_seconds(hours, minutes, seconds)

def generate_unix_timestamp(minutes=0, hours=0, days=0, seconds=0):
    # 获取当前时间
    now = datetime.fromtimestamp(int(client.get_unix_time().epoch_seconds))

    # 根据传入的时间差（分钟、小时、天、秒）计算目标时间
    target_time = now - timedelta(minutes=minutes, hours=hours, days=days, seconds=seconds)

    # 转换为 UNIX 时间戳（秒）
    unix_timestamp = int(time.mktime(target_time.timetuple()))

    return str(unix_timestamp)


