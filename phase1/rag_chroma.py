"""
rag_chroma.py —— Day 14：补齐 Phase 2 三个缺口
  1) 向量库：用 Chroma（本地持久化，取代 numpy 内存矩阵）
  2) 文档处理：支持 .txt 与 .pdf（pypdf 解析）
  3) 引用来源：检索块带 source/chunk_idx 元数据，回答末尾标注出处

复用 Day12 的本地 bge 检索能力（rag.get_embedder / QUERY_PREFIX / chunk_text），
不改动 rag.py / rag_cli.py。
"""
import os
# 镜像站：国内连 huggingface.co 超时；必须在 import sentence_transformers 之前设置
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import sys
_BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _BASE)

import chromadb
import pypdf
import rag                       # 复用 chunk_text / get_embedder / QUERY_PREFIX
from call_llm import chat

# ---- 模块级 bge 单例：避免多次加载 torch 模型 ----
_EMB = None


def _get_embedder():
    global _EMB
    if _EMB is None:
        _EMB = rag.get_embedder()
    return _EMB


class BGEEmbeddingFunction:
    """Chroma 的 embedding 函数：文档入库用标准 doc 编码（不加 query 前缀）。
    查询时由 retrieve() 单独带前缀编码，保证 bge 检索质量。"""

    def __call__(self, input):
        # input: list[str]
        vecs = _get_embedder().encode(list(input), normalize_embeddings=True)
        return vecs.tolist()


# ----------------------------------------------------------------------------
# 文档加载：txt / pdf
# ----------------------------------------------------------------------------
def load_file(path):
    """返回单个文件的纯文本。支持 .txt 与 .pdf。"""
    if path.lower().endswith(".pdf"):
        reader = pypdf.PdfReader(path)
        parts = [(p.extract_text() or "") for p in reader.pages]
        return "\n".join(parts)
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_kb(file_paths):
    """多文件 → (chunks, metadatas)。每块记录来源文件名与块序号。"""
    chunks, metas = [], []
    idx = 0
    for fp in file_paths:
        text = load_file(fp)
        src = os.path.basename(fp)
        for c in rag.chunk_text(text):
            chunks.append(c)
            metas.append({"source": src, "chunk_idx": idx})
            idx += 1
    return chunks, metas


# ----------------------------------------------------------------------------
# Chroma 建库 / 检索
# ----------------------------------------------------------------------------
def build_collection(chunks, metas, name="rag_kb",
                     persist_dir=os.path.join(_BASE, "chroma_db")):
    client = chromadb.PersistentClient(path=persist_dir)
    if name in [c.name for c in client.list_collections()]:
        client.delete_collection(name)
    coll = client.create_collection(name, embedding_function=BGEEmbeddingFunction())
    coll.add(
        documents=chunks,
        ids=[f"c{i}" for i in range(len(chunks))],
        metadatas=metas,
    )
    return coll


def retrieve(coll, query, top_k=3):
    """查询时给 query 加 bge 前缀编码，与 doc 编码区分，检索更准。"""
    q_vec = _get_embedder().encode(
        [rag.QUERY_PREFIX + query], normalize_embeddings=True
    )[0].tolist()
    res = coll.query(
        query_embeddings=[q_vec],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    out = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        out.append({
            "content": doc,
            "source": meta["source"],
            "chunk_idx": meta["chunk_idx"],
            "distance": round(dist, 4),
        })
    return out


# ----------------------------------------------------------------------------
# 生成 + 引用来源
# ----------------------------------------------------------------------------
def answer(query, coll, top_k=3, debug=False):
    hits = retrieve(coll, query, top_k)
    ctx = "\n\n".join(
        f"[资料{i+1}]（来源：{h['source']} 块#{h['chunk_idx']}）\n{h['content']}"
        for i, h in enumerate(hits)
    )
    prompt = (
        "你是一名消费金融合规顾问。仅依据下面的【知识库内容】回答问题；\n"
        "若引用了某条资料，请在句末用括号标注（来源：文件名 块#编号）；\n"
        "知识库未覆盖的内容请回答'知识库未提及'，不要编造。\n\n"
        f"【知识库内容】\n{ctx}\n\n"
        f"【问题】{query}"
    )
    if debug:
        print("=== PROMPT ===\n", prompt, "\n=== END ===")
    reply = chat([{"role": "user", "content": prompt}])

    refs = "\n".join(
        f"  · {h['source']} 块#{h['chunk_idx']}（相似度距离 {h['distance']}）："
        f"{h['content'][:60]}..."
        for h in hits
    )
    return f"{reply}\n\n【参考来源】\n{refs}"


if __name__ == "__main__":
    files = ["kb_compliance.txt", "sample_policy.pdf"]
    paths = [os.path.join(_BASE, f) for f in files]
    chunks, metas = load_kb(paths)
    print(f"共切分 {len(chunks)} 块，建 Chroma 库...")
    coll = build_collection(chunks, metas)

    questions = [
        "营销短信可以用'秒批'这类词吗？",
        "助贷业务的综合融资成本有什么限制？",
        "sample_policy.pdf 里对风险提示是怎么要求的？",
    ]
    for q in questions:
        print("\n" + "=" * 60)
        print(">>> 问：", q)
        print(answer(q, coll))
