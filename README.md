# ai-learning-log

AI 应用工程师学习路线 Phase 0 练习仓库（Day 1-6）。

## 已完成
- Day 1：跑通第一个 DeepSeek API 调用
- Day 2：temperature / token 概念与实验
- Day 3：system 角色设定
- Day 4：结构化输出（JSON mode）
- Day 5：few-shot 样例约束
- Day 6：综合实战 —— 行业新闻摘要 + 风险提示 + 实体抽取
- Day 7：GitHub 收尾（本仓库）

## 文件说明
| 文件 | 内容 |
|---|---|
| `first_call.py` | 第一个 DeepSeek API 调用 |
| `temperature_test.py` | temperature / token 实验 |
| `system_prompt_test.py` | system 角色设定对比 |
| `json_test.py` | 结构化输出 JSON |
| `fewshot_test.py` | few-shot 样例约束 |
| `day6_news_analyzer.py` | 综合实战：新闻摘要+风险+实体抽取 |
| `笔记_ai.md` | 学习笔记 |

## 本地运行
1. `pip install openai python-dotenv`
2. 在项目根目录创建 `.env`，写入 `DEEPSEEK_API_KEY=你的key`
3. `python first_call.py`

> ⚠️ API Key 仅保留在本地 `.env`，该文件已被 `.gitignore` 排除，不会上传到仓库。
