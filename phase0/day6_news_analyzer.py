import os, json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

system = (
    "你是金融/信贷行业资深分析师,擅长从新闻中提炼要点与风险。"
    "必须输出合法 JSON 格式。"
)

# few-shot: 给一条范例,模型照着输出结构
few_shot = [
    {"role": "user", "content": "【新闻】某地金融局通报,3家小贷公司因暴力催收被处罚,涉及电话骚扰与泄露个人信息。"},
    {"role": "assistant", "content": json.dumps({
        "summary": [
            "当地监管加大对小贷催收违规的打击力度",
            "违规集中在电话骚扰与信息泄露两类",
            "涉事机构面临罚款与整改"
        ],
        "risks": [
            "短信/外呼营销需严控合规,避免骚扰投诉",
            "客户信息保护不足将触发监管风险"
        ]
    }, ensure_ascii=False)},
]

def analyze_news(text):
    messages = [{"role": "system", "content": system}] + few_shot + [{"role": "user", "content": text}]
    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3,   # 稳定输出,适合摘要类
        )
        return json.loads(resp.choices[0].message.content)
    except json.JSONDecodeError:
        return {"error": "JSON 解析失败,请重试"}

# ===== 把下面这段换成你自己的行业新闻 =====
news = """8月11日,安徽省通信管理局通报了一批侵害用户权益的App,其中阜阳元一小额贷款有限公司开发的"省心借"因违规收集个人信息被点名。公告称,该局近期对省内App进行拨测检查,发现21款App存在违法违规收集使用个人信息的问题,并于6月23日下达责令改正通知书。截至目前,尚有"省心借"等6款App未完成整改,相关开发者应在8月17日前落实整改,逾期将依法处置。公开信息显示,元一小贷成立于2012年,注册资本1亿元;其法人同时担任一家融资担保公司监事,关联机构近期也密集备案了多款借款类App。此前已有小贷公司旗下多款借款App在数月内先后因个人信息保护问题被监管通报。"""

result = analyze_news(news)
print("=== 要点摘要 ===")
for i, s in enumerate(result.get("summary", []), 1):
    print(f"{i}. {s}")
print("\n=== 风险提示 ===")
for i, r in enumerate(result.get("risks", []), 1):
    print(f"{i}. {r}")