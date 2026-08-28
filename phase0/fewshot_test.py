import os, json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

system = ("你是小贷营销文案专家,文案70字内,含退订回T,禁用绝对化用语。"
          "必须输出合法 JSON 格式。")


# 3条优质样例:用户需求 → 标准回答(prompt+回答成对)
few_shot = [
    {"role": "user",      "content": "产品:极速贷,人群:上班族"},
    {"role": "assistant", "content": '{"sms":"【极速贷】工资未到账?最高20万秒审批,息费透明,退订回T","score":9,"reason":"直击痛点且合规"}'},
    {"role": "user",      "content": "产品:现金分期,人群:个体户"},
    {"role": "assistant", "content": '{"sms":"【现金分期】周转不灵?3万随借随还,当天到账,退订回T","score":9,"reason":"场景明确"}'},
    {"role": "user",      "content": "产品:车主贷,人群:有车族"},
    {"role": "assistant", "content": '{"sms":"【车主贷】爱车也能周转,最高50万当日放款,退订回T","score":8,"reason":"突出额度优势"}'},
]

target = [{"role": "user", "content": "产品:教育分期,人群:家长"}]

def gen(use_few_shot=False):
    messages = [{"role": "system", "content": system}]
    if use_few_shot:
        messages += few_shot
    messages += target
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    return resp.choices[0].message.content

print("=== 无 few-shot ===")
print(gen(use_few_shot=False))
print("\n=== 有 few-shot ===")
print(gen(use_few_shot=True))
