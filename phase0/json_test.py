import os, json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

system = ("你是小贷营销文案专家。规则:"
          "1)短信70字内 2)禁用'最''第一''绝对'等绝对化用语 3)必须含'退订回T'")

user = ('为产品"极速贷"生成一条营销短信,严格按JSON格式返回,'
        '字段:{"sms": "文案内容", "score": 评分0-10整数, "reason": "评分理由"}')

resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ],
    response_format={"type": "json_object"},  # 关键:强制 JSON 输出
    temperature=0.4,
)

raw = resp.choices[0].message.content
print("原始返回:", raw)

try:
    data = json.loads(raw)  # 解析成字典
    print("文案:", data["sms"])
    print("评分:", data["score"])
    print("理由:", data["reason"])
except json.JSONDecodeError:
    print("⚠️ 解析失败,原始内容:", raw)
