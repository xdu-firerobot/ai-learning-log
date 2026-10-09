"""
call_llm.py - 可复用的 LLM 调用模块（项目①营销文案生成器的地基）
封装内容（对应 Day 1-7 学过的工程化要点）：
  - 从 .env 读取 DeepSeek API Key（密钥与代码分离）
  - chat():      基础调用 + 异常重试（网络抖动自动重跑）
  - chat_json(): 强制 JSON 输出 + 解析兜底（json_object 硬约束 + try/except）
  - chat_stream():流式输出（打字机效果，做交互界面时用）
  - Conversation: 多轮对话管理（messages 自动累加，不用手动拼）

用法见文件底部 __main__ 示例。
"""

import os
import time
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

DEFAULT_MODEL = "deepseek-chat"


def chat(messages, temperature=0.4, response_format=None, max_retries=3, retry_delay=2):
    """
    基础调用 + 异常重试。
    messages: [{"role": "system"/"user"/"assistant", "content": "..."}, ...]
    response_format: 如 {"type": "json_object"} 强制 JSON，可省略
    返回: 模型文本（str）
    """
    last_err = None
    for attempt in range(max_retries):
        try:
            kwargs = {
                "model": DEFAULT_MODEL,
                "messages": messages,
                "temperature": temperature,
            }
            if response_format:
                kwargs["response_format"] = response_format
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content
        except Exception as e:
            last_err = e
            print(f"⚠️ 调用失败(第{attempt + 1}次): {e}")
            time.sleep(retry_delay)
    raise RuntimeError(f"LLM 调用失败 {max_retries} 次，最后错误: {last_err}")


def chat_json(messages, temperature=0.4, max_retries=3):
    """
    强制 JSON 输出 + 解析兜底。
    返回: 解析后的字典(dict)；解析失败返回 None。
    关键点: DeepSeek 要求 prompt 中出现 "json" 字样，否则 json_object 直接拒，
            这里自动补齐一个 system 约束保证通过。
    """
    # 自动检查: prompt 里是否已含 "json" 字样
    has_json_word = any(
        "json" in m.get("content", "").lower() for m in messages
    )
    if not has_json_word:
        if messages and messages[0]["role"] == "system":
            messages[0]["content"] += "\n请务必以合法JSON格式输出。"
        else:
            messages.insert(0, {"role": "system", "content": "请务必以合法JSON格式输出。"})

    raw = chat(
        messages,
        temperature=temperature,
        response_format={"type": "json_object"},
        max_retries=max_retries,
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON 解析失败: {e}\n原始返回前200字: {raw[:200]}")
        return None


def chat_stream(messages, temperature=0.4):
    """流式输出（打字机效果）。用于需要实时显示的场景。"""
    resp = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages,
        temperature=temperature,
        stream=True,
    )
    for chunk in resp:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
    print()  # 收尾换行


class Conversation:
    """多轮对话管理: 自动维护 messages 历史，模型无需"记忆"。"""

    def __init__(self, system=None):
        self.messages = []
        if system:
            self.messages.append({"role": "system", "content": system})

    def ask(self, user_content, temperature=0.4):
        self.messages.append({"role": "user", "content": user_content})
        reply = chat(self.messages, temperature)
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def history(self):
        return self.messages


if __name__ == "__main__":
    # 示例 1: 普通调用
    print("=== 普通调用 ===")
    print(chat([{"role": "user", "content": "用一句话介绍你自己"}]))

    # 示例 2: JSON 调用（无需手动加 json 字样，模块自动补齐）
    print("\n=== JSON 调用 ===")
    data = chat_json([
        {"role": "user", "content": '为产品"极速贷"生成一条短信，返回{"sms":"文案","score":0-10}'}
    ])
    print(data)

    # 示例 3: 多轮对话
    print("\n=== 多轮对话 ===")
    conv = Conversation(system="你是小贷文案专家")
    print(conv.ask("写一条贷款短信"))
    print(conv.ask("换一个更口语化的"))

    # 示例 4: 流式输出
    print("\n=== 流式输出 ===")
    chat_stream([{"role": "user", "content": "用三个短句介绍消费分期"}])