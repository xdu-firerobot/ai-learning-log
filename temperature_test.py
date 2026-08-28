import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

def ask(question, temperature):
    return client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": question}],
        temperature=temperature,
    )

question = "给'极速贷'写一条吸引上班族的营销短信,30字以内"

for temp in [0.2, 0.7, 1.4]:
    print(f"\n=== temperature={temp} (每个跑3遍) ===")
    for i in range(3):
        resp = ask(question, temp)
        # print(resp.choices)
        # print(resp.choices[0])
        # print(resp.choices[0].message)
        text = resp.choices[0].message.content
        u = resp.usage
        print(f"第{i+1}遍: {text}")
        print(f"  token: 入{u.prompt_tokens}/出{u.completion_tokens}/共{u.total_tokens}")
