import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

def ask(question, system_prompt=None, temperature=0.7):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": question})
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content

question = "写一条小贷营销短信"

print("=== 无角色设定 ===")
print(ask(question))

print("\n=== 有角色:资深文案专家 ===")
system = ("你是小贷行业资深短信文案专家,熟悉监管合规要求。文案必须:"
          "1)70字以内 2)禁用'最''第一''绝对'等绝对化用语 "
          "3)必须包含'退订回T' 4)语气专业克制")
print(ask(question, system_prompt=system))

print("\n=== 有角色:严厉风控审核员 ===")
system2 = "你是严谨的风控合规审核员。请审查'小贷营销短信'的合规风险,逐条列出隐患,语气冷峻。"
print(ask(question, system_prompt=system2))
