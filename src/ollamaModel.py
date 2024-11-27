import requests
import json

def call_llama_model(prompt):
    url = "http://localhost:11434/api/generate"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3.1",
        "prompt": prompt,
        "system": "",  # 可选，系统提示词
        "options": {
            "temperature": 0.0,
            "max_length": 100,
            "stop": ["</s>"]
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, stream=True)

        if response.status_code == 200:
            # 逐行读取生成的文本
            generated_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    data = line.strip()
                    # Ollama的API返回的是JSON行，需要解析
                    json_data = json.loads(data)
                    # 获取生成的文本
                    token = json_data.get('response', '')
                    generated_text += token
            return generated_text
        else:
            print("Error:", response.status_code, response.text)
            return None
    except Exception as e:
        print("Exception occurred:", str(e))
        return None

# 示例使用
if __name__ == "__main__":
    user_input = "Market data for XRP-USD: Best Bid: 1.4092, Best Ask: 1.4093, Time: 2024-11-27 00:00:15.907375, Recent Trades:trade_0 1.4092500000000001 1601.173499, trade_1 1.4092500000000001 1514.516414, trade_2 1.4092500000000001 1206.254036, trade_3 1.4092500000000001 1247.987576, trade_4 1.4092500000000001 1913.148517, trade_5 1.4092500000000001 1770.266321, trade_6 1.4092500000000001 1520.351709, trade_7 1.4092500000000001 1643.75, trade_8 1.4092500000000001 2307.986228, trade_9 1.4092500000000001 6987.292423, trade_10 1.4092500000000001 16128.973803, trade_11 1.4092500000000001 8227.119129, trade_12 1.4092500000000001 4919.149142, trade_13 1.4092500000000001 2653.918026, trade_14 1.4092500000000001 4444.360828, trade_15 1.4092500000000001 2224.188474, trade_16 1.4092500000000001 1932.522359, trade_17 1.4092500000000001 3629.241198, trade_18 1.4092500000000001 1454.030359, trade_19 1.4092500000000001 3079.301198, trade_20 1.4092500000000001 5310.087088, trade_21 1.4092500000000001 12331.461114, trade_22 1.4092500000000001 9748.753285, trade_23 1.4093 887.154036, trade_24 1.4093 1368.4, trade_25 1.4093 3462.264919, trade_26 1.4093 10427.549729, trade_27 1.4093 525.34, trade_28 1.4092500000000001 5310.627534, trade_29 1.4092500000000001 35556.654686, trade_30 1.4092500000000001 1707.25, trade_31 1.4092500000000001 9341.84626, trade_32 1.4092500000000001 525.68, trade_33 1.4092500000000001 529.5, trade_34 1.4092500000000001 525.68, trade_35 1.4093 526.44, trade_36 1.4093499999999999 1370.19, trade_37 1.4093499999999999 526.35, trade_38 1.4093499999999999 12538.75, trade_39 1.4093499999999999 526.35, trade_40 1.4093499999999999 529.46, trade_41 1.4094 1374.2, trade_42 1.4094 1370.1, trade_43 1.4094 525.68, trade_44 1.4094 1369.27, trade_45 1.4094 843.75, trade_46 1.4094 530.61, trade_47 1.4094000000000002 548.261317, trade_48 1.4094000000000002 2685.78, trade_49 1.4094 525.03, trade_50 1.4094 530.45, trade_51 1.4094 524.91, trade_52 1.4094 530.45, trade_53 1.4094 524.4, trade_54 1.40945 524.4, trade_55 1.4097 532.2, trade_56 1.40985 532.42, trade_57 1.40985 532.4, trade_58 1.40985 532.4, trade_59 1.40985 559.98284, trade_60 1.40985 1414.45, trade_61 1.4099 524.45, trade_62 1.40995 524.45, trade_63 1.4100000000000001 524.45, trade_64 1.4100000000000001 4.772779, trade_65 1.4100000000000001 7.539214, trade_66 1.4100000000000001 524.16, trade_67 1.4100000000000001 265.980438, trade_68 1.4100000000000001 598.955129, trade_69 1.41 524.16, trade_70 1.41 524.21, trade_71 1.4099499999999998 10.699765, trade_72 1.4097 392.0, trade_73 1.40965 827.973758, trade_74 1.40965 676.363701, trade_75 1.4095 594.06, trade_76 1.4095 594.06, trade_77 1.4095 594.06, trade_78 1.4093499999999999 35717.990419, trade_79 1.4093499999999999 208.139867, trade_80 1.4093499999999999 166.889474, trade_81 1.4093 571.0, trade_82 1.4093 0.74388, trade_83 1.4093 2.379591, trade_84 1.4093 100.0, trade_85 1.40915 6.907312, trade_86 1.40875 560.66, trade_87 1.4087 1864.350105, trade_88 1.4087 266.284916, trade_89 1.40865 554.42, trade_90 1.40865 524.71156, trade_91 1.40865 74.120017, trade_92 1.4083 35.872361, trade_93 1.40825 53.71581, trade_94 1.40825 15.203809, trade_95 1.40765 266.13218, trade_96 1.40735 0.253679, trade_97 1.4073 0.724106, trade_98 1.4073 0.531648, trade_99 1.4073 64.580941, Current XRP price: 1.4092500000000001 USD.XRP Balance: 85.06172377828017 XRP.USD Balance: 0.0186755198754 USD. You are an expert day trader utilizing a KNN prediction model for market analysis. Recent price movements indicate either an upward or downward trend. If the trend is positive and strong, respond with BUY. If the trend is negative and strong, respond with SELL. If the trend is unclear or weak, respond with HOLD. Based on this prediction and your strategy, should we BUY, SELL, or HOLD? Respond with one word: BUY, SELL, or HOLD."
    response = call_llama_model(user_input)
    if response:
        print("模型回复：", response)
    else:
        print("调用模型失败。")

    print(type(response))
