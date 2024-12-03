import os
import requests

# 定义 Webhook URL 文件路径
WEBHOOK_FILE_PATH = r'J:\Trading\webhooks\Discord\trading-info\Trade_Alert_Bot.txt'

def get_webhook_url():
    """
    从文件中读取 Discord Webhook URL
    """
    # 检查文件是否存在
    if not os.path.exists(WEBHOOK_FILE_PATH):
        raise FileNotFoundError(f"Webhook URL 文件未找到：{WEBHOOK_FILE_PATH}")

    # 读取 Webhook URL
    with open(WEBHOOK_FILE_PATH, 'r', encoding='utf-8') as f:
        webhook_url = f.read().strip()

    if not webhook_url:
        raise ValueError("Webhook URL 为空，请检查文件内容。")

    return webhook_url

def send_discord_notification(message):
    """
    使用 Discord Webhook 发送通知
    """
    webhook_url = get_webhook_url()
    data = {
        "content": message  # 消息内容
    }
    try:
        response = requests.post(webhook_url, json=data)
        if response.status_code == 204:
            print("已发送通知到 Discord。")
        else:
            print(f"发送通知失败，状态码：{response.status_code}")
    except Exception as e:
        print(f"发送通知失败：{e}")


if __name__ == "__main__":
    send_discord_notification("Test Message. 测试发送。")