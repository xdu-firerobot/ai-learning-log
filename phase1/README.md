# Phase1 项目①：贷款短信合规生成器

基于 DeepSeek API 的贷款营销短信生成器，内置「生成 + 独立审核」双模型协作，
落地《金融产品网络营销管理办法》(2026-09-30 施行) 与助贷新规的合规约束。

## 架构：三关防线（漏杀 + 误杀双控）

| 关 | 模块 | 类型 | 作用 |
|---|---|---|---|
| 第1关 | 黑名单硬拦截 | 代码硬约束 | 输入含禁词（黑户/秒批/无视征信…）直接驳回，不调 API |
| 第2关 | generator 生成自检 | LLM 软约束 | 生成结构化短信 + 模型自判 compliant |
| 第3关 | reviewer 独立审核 | LLM 软约束 | 第二个独立调用交叉挑刺，标准与生成方对齐 |

> 设计核心：确定性红线用代码管（硬约束），不确定的创作/审核交给 LLM（软约束）。
> 生成方和审核方是两个独立 LLM 调用，互相不串供 —— Multi-Agent 雏形。

## 文件结构

    phase1/
    ├── call_llm.py      # 地基：chat / chat_json / chat_stream / Conversation
    ├── generator.py     # 生成器 + 黑名单 + pipeline() 三关串联
    ├── reviewer.py      # 独立审稿人：review_sms()
    └── README.md        # 本文件

## 运行

    conda activate ai
    cd C:\Users\55493\Desktop\work\deepseek
    python phase1/generator.py

依赖：openai（DeepSeek 兼容 SDK）、python-dotenv；API Key 存于根目录 `.env`：

    DEEPSEEK_API_KEY=你的key

## 输出 JSON 结构

生成方：
    {"title": "标题", "content": "正文", "score": 8, "compliant": true, "risk_reason": ""}

审稿方：
    {"pass": true, "issues": [], "suggestion": "通过理由/修改建议"}

pipeline 终审结论：
    {"final": "approve"|"reject"|"error", "stage": "generate"|"review", ...}

## 设计要点（面试可讲）

1. 软硬约束分离：关键合规边界用代码黑名单卡死，不依赖模型自觉。
2. 多 Agent 标准对齐：审稿方审核维度 = 生成方硬约束，且 pass=true 禁止加码，避免 100% 误杀。
3. domain know-how 落地：禁诱导话术、强制利率披露 + 风险提示，是金融营销独有壁垒。

## 局限与下一步

- 审稿质量依赖 prompt 调优，极端样本仍需人工复核。
- 下一步：接向量库做 RAG（合同条款检索）、批量从 CSV 读产品并导出审核台账。
