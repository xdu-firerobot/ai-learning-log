import json
from call_llm import chat_json

SYSTEM_PROMPT = """你是一名合规的消费金融/贷款营销短信文案专家。

# 任务
根据产品信息撰写一条合规营销短信，仅以JSON格式返回。

# 合规硬约束（违反任意一条即判 compliant=false）
0. 输入自检优先：若产品信息中的卖点或目标人群本身违规（如"黑户可贷""无视征信""秒批"，
   或目标人群为"征信差人群"等以违规获客为导向的表述），必须直接返回 compliant=false
   并在 risk_reason 说明原因，禁止将其改写为合规文案。
1. 禁止诱导/承诺话术："秒批""低至X%""无费用""黑户可贷""无视征信""100%通过""guaranteed""零门槛""免审核"。
2. 不得承诺审批结果，不得夸大额度或利率优势。
3. 必须展示真实年化利率(APR)区间或明确费率说明，不得隐瞒融资成本。
4. 正文必须含风险提示，如"借贷有风险，理性消费，按时还款"。
5. 正文不超过70个汉字（含标点）。
6. 符合《金融产品网络营销管理办法》(2026-09-30施行)及助贷新规，由持牌机构开展，不得变相高息。

# 输出结构（仅返回JSON）
{
  "title": "文案标题≤15字",
  "content": "短信正文≤70字含风险提示",
  "score": 0-10整数,
  "compliant": true或false,
  "risk_reason": "不合规写明原因，合规则空串"
}
"""

FEWSHOTS = [
    {"role": "user",      "content": """产品信息：{"product":"极速贷","amount":"最高20万","term":"3-12期","selling_point":"随借随还","target":"上班族"}
请生成合规短信，返回JSON。"""},
    {"role": "assistant", "content": """{
  "title": "上班族应急周转",
  "content": "【极速贷】最高20万，3-12期随借随还，年化利率7.2%-18%。借贷有风险，请根据还款能力合理借贷。",
  "score": 8,
  "compliant": true,
  "risk_reason": ""
}"""},
    {"role": "user",      "content": """产品信息：{"product":"速通花","amount":"不限","term":"灵活","selling_point":"黑户也能下","target":"征信差人群"}
请生成合规短信，返回JSON。"""},
    {"role": "assistant", "content": """{
  "title": "（不适用）",
  "content": "（无法生成合规文案）",
  "score": 0,
  "compliant": false,
  "risk_reason": "卖点含'黑户也能下'属违规诱导话术，且'不限额度''灵活期限'夸大承诺，违反营销管理办法，不予生成。"
}"""},
]
BANNED_WORDS = ["黑户", "秒批", "无视征信", "100%通过", "免审核", "零门槛"]


def generate_sms(product, amount, term, selling_point, target):
    hit = [w for w in BANNED_WORDS if w in selling_point or w in target]
    if hit:
        return {"compliant": False, "risk_reason": f"输入含违规词：{hit}", "score": 0}
    info = {
        "product": product, "amount": amount, "term": term,
        "selling_point": selling_point, "target": target
    }
    user_content = (
        "产品信息：" + json.dumps(info, ensure_ascii=False) +
        " 请生成合规短信，返回JSON。"
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += FEWSHOTS
    messages.append({"role": "user", "content": user_content})

    data = chat_json(messages)          # 返回 dict 或 None
    if data is None:
        return {"error": "生成失败"}
    return data

def batch_generate(products):
    results = []
    for p in products:
        results.append(generate_sms(**p))
    return results

if __name__ == "__main__":
    samples = [
        {"product":"极速贷","amount":"最高20万","term":"3-12期","selling_point":"随借随还","target":"上班族"},
        {"product":"生意金","amount":"最高50万","term":"6-24期","selling_point":"商户专属","target":"小微店主"},
        {"product":"速通花","amount":"不限","term":"灵活","selling_point":"黑户也能下","target":"征信差人群"},
    ]
    for r in batch_generate(samples):
        print(r)
