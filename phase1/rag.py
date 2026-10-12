"""
Day12 项目②：本地 RAG 知识库（数据不出本机）
流程：切分知识文档 → 本地模型转向量 → 存内存 → 提问检索相似块 → DeepSeek 基于检索内容回答

分工：
- 检索/向量：本地 bge 嵌入模型（sentence-transformers，离线）
- 生成/回答：DeepSeek（call_llm.chat，你已会调）
"""
import os
# 国内直连 huggingface.co 会超时(WinError 10060)，改走镜像站
# 注意：必须在 import sentence_transformers 之前设置才生效
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
import numpy as np
from sentence_transformers import SentenceTransformer
from call_llm import chat

# ---------- 1. 初始化本地嵌入模型（首次会自动下载 bge-small-zh，约95MB）----------
MODEL_NAME = "BAAI/bge-small-zh-v1.5"
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(MODEL_NAME)
    return _embedder

# bge 系列对"查询"建议加前缀，检索效果更好
QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："

# ---------- 2. 文本分块（带重叠，避免切断语义）----------
def chunk_text(text, max_len=200, overlap=50):
    """按字数切分，overlap 让相邻块共享一部分上下文。"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_len
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return chunks

# ---------- 3. 建索引：把所有块转成向量 ----------
def build_index(chunks):
    model = get_embedder()
    vectors = model.encode(chunks, normalize_embeddings=True)
    return np.array(vectors, dtype="float32")   # 归一化后点积=余弦相似度

# ---------- 4. 检索：提问转向量，取最相似的 top_k 块 ----------
def retrieve(query, chunks, index, top_k=3):
    model = get_embedder()
    q_vec = model.encode([QUERY_PREFIX + query], normalize_embeddings=True)[0]
    sims = index @ q_vec                      # 向量点积 = 余弦相似度
    top_idx = np.argsort(-sims)[:top_k]       # 相似度从高到低取前 top_k
    return [chunks[i] for i in top_idx]

# ---------- 5. 回答：检索到的块拼进 prompt，交给 DeepSeek ----------
def answer(query, chunks, index, top_k=3):
    hits = retrieve(query, chunks, index, top_k)
    context = "\n---\n".join(hits)
    prompt = (
        "你是一名消费金融合规顾问，仅依据下面提供的【知识库内容】回答问题，"
        "若知识库未覆盖请回答'知识库未提及'，不要编造。\n\n"
        f"【知识库内容】\n{context}\n\n"
        f"【问题】{query}"
    )
    print(prompt)
    return chat([{"role": "user", "content": prompt}])

# ---------- 6. 装载知识库并建索引 ----------
def load_kb(path="kb_compliance.txt"):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    chunks = chunk_text(text)
    index = build_index(chunks)
    return chunks, index

if __name__ == "__main__":
    kb_path = os.path.join(os.path.dirname(__file__), "kb_compliance.txt")
    chunks, index = load_kb(kb_path)
    print(f"知识库已切分为 {len(chunks)} 块，向量维度 {index.shape[1]}\n")

    questions = [
        "贷款短信里写'秒批'合规吗？",
        "营销短信必须包含什么风险提示？",
        "助贷业务综合融资成本有什么限制？",
    ]
    for q in questions:
        print(f"问：{q}")
        print(f"答：{answer(q, chunks, index)}\n{'-'*60}")
