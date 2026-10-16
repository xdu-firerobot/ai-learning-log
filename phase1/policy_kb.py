"""
policy_kb.py —— Day 15：项目② 小贷行业政策知识库问答（框架 + 增量建库 + 切分实验）
复用 Day14 的 Chroma 能力（rag_chroma：load_file/load_kb/BGEEmbeddingFunction/retrieve）。

两个关键升级（相对 rag_chroma.py）：
  1) 增量建库：get_or_create + 稳定 id（来源+内容哈希），只 add 库里没有的块。
     ——修复 rag_chroma 每次 delete+create 全量重建的瑕疵，真正兑现"持久化省时"。
  2) 检索兜底：top1 距离过大或模型答"知识库未提及"时，给出补充提示，不编造。

切分对比实验：chunk_compare() 在 200/400 字两种粒度下分别建临时库，
对比同一批问题的 top1 命中来源，验证 chunk 大小对检索的影响。
"""
import os
import sys
import glob
import hashlib

_BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _BASE)

import chromadb
import rag
import rag_chroma as rc
from call_llm import chat, chat_stream

DOCS_DIR = os.path.join(_BASE, "policy_docs")
PERSIST = os.path.join(_BASE, "chroma_policy")
COLLECTION = "policy_kb"
# 检索兜底阈值：bge 归一化向量欧氏距离，越接近 0 越相似；
# 经验上 > 1.3 基本可判定"知识库无相关内容"。
FALLBACK_DIST = 1.3


def stable_id(source, chunk_idx, content):
    """稳定 id：文件没变、内容没变 → id 不变 → 不重算；内容变了 → id 变 → 触发更新。"""
    h = hashlib.md5((source + "|" + content).encode("utf-8")).hexdigest()[:12]
    return f"{source}#{chunk_idx}#{h}"


def build_incremental(rebuild=False):
    """增量建库：已有块从磁盘加载不重算，只 add 新增块。"""
    client = chromadb.PersistentClient(path=PERSIST)
    if rebuild and COLLECTION in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION)
    coll = client.get_or_create_collection(
        COLLECTION, embedding_function=rc.BGEEmbeddingFunction()
    )

    paths = sorted(glob.glob(os.path.join(DOCS_DIR, "*")))
    paths = [p for p in paths if p.lower().endswith((".txt", ".pdf"))]
    chunks, metas = rc.load_kb(paths)

    ids = [stable_id(m["source"], m["chunk_idx"], c)
           for c, m in zip(chunks, metas)]

    # 库里已存在的 id（不重算）
    existing = set()
    if ids:
        try:
            existing = set(coll.get(ids=ids, include=[])["ids"])
        except Exception:
            existing = set()

    add_docs, add_ids, add_meta = [], [], []
    for c, m, iid in zip(chunks, metas, ids):
        if iid not in existing:
            add_docs.append(c)
            add_ids.append(iid)
            add_meta.append(m)

    added = 0
    if add_docs:
        B = 500  # 分批写入，避免单次过大
        for i in range(0, len(add_docs), B):
            coll.add(documents=add_docs[i:i + B],
                     ids=add_ids[i:i + B],
                     metadatas=add_meta[i:i + B])
        added = len(add_docs)

    return coll, coll.count(), added


def answer(query, coll, top_k=3, debug=False, stream=False):
    hits = rc.retrieve(coll, query, top_k)
    ctx = "\n\n".join(
        f"[资料{i+1}]（来源：{h['source']} 块#{h['chunk_idx']}）\n{h['content']}"
        for i, h in enumerate(hits)
    )
    prompt = (
        "你是一名小贷/消费金融政策问答助手。仅依据【知识库内容】回答用户关于监管政策的问题；\n"
        "若引用了某条资料，请在句末用括号标注（来源：文件名 块#编号）；\n"
        "知识库未覆盖的内容请回答'知识库未提及'，不要编造。\n\n"
        f"【知识库内容】\n{ctx}\n\n"
        f"【问题】{query}"
    )
    if debug:
        print("=== PROMPT ===\n", prompt, "\n=== END ===")

    if stream:
        print("答：", end="", flush=True)          # 先打个前缀
        chat_stream([{"role": "user", "content": prompt}])  # 逐字流出
        reply = ""                                  # 流式拿不到文本
    else:
        reply = chat([{"role": "user", "content": prompt}])

    best = hits[0]["distance"] if hits else 99
    if best > FALLBACK_DIST or "知识库未提及" in reply:
        reply += ("\n\n（提示：当前知识库未检索到足够相关的政策条文，"
                  "建议补充对应监管文件或咨询合规/法务。）")

    refs = "\n".join(
        f"  · {h['source']} 块#{h['chunk_idx']}（距离 {h['distance']}）："
        f"{h['content'][:50]}..."
        for h in hits
    )
    return f"{reply}\n\n【参考来源】\n{refs}"


def chunk_compare(questions, sizes=(200, 400), top_k=3):
    """切分对比实验：不同 max_len 下建独立临时库，比较 top1 命中来源。"""
    exp_dir = PERSIST + "_exp"
    results = {}
    for sz in sizes:
        name = f"exp_chunk_{sz}"
        client = chromadb.PersistentClient(path=exp_dir)
        if name in [c.name for c in client.list_collections()]:
            client.delete_collection(name)
        coll = client.create_collection(
            name, embedding_function=rc.BGEEmbeddingFunction()
        )
        paths = sorted(glob.glob(os.path.join(DOCS_DIR, "*")))
        paths = [p for p in paths if p.lower().endswith((".txt", ".pdf"))]
        chunks, metas = [], []
        idx = 0
        for fp in paths:
            text = rc.load_file(fp)
            src = os.path.basename(fp)
            for c in rag.chunk_text(text, max_len=sz, overlap=50):
                chunks.append(c)
                metas.append({"source": src, "chunk_idx": idx})
                idx += 1
        coll.add(documents=chunks,
                 ids=[f"c{i}" for i in range(len(chunks))],
                 metadatas=metas)
        rows = []
        for q in questions:
            h = rc.retrieve(coll, q, top_k)[0]
            rows.append((q, h["source"], h["distance"]))
        results[sz] = rows
    return results


if __name__ == "__main__":
    rebuild = "--rebuild" in sys.argv
    coll, total, added = build_incremental(rebuild=rebuild)
    print(f"[建库] 总块数={total}，本次新增={added}"
          f"{'（已全量重建）' if rebuild else '（增量）'}")

    qs = [
        "互联网贷款合作方的出资比例不得低于多少？",
        "营销短信可以用'秒批'吗？",
        "民间借贷利率司法保护上限是多少？",
        "采集征信信息需要取得本人同意吗？",
        "地方法人银行能跨地区开展互联网贷款吗？",
    ]
    for q in qs:
        print("\n" + "=" * 60)
        print(">>> 问：", q)
        print(answer(q, coll, stream=True))

    print("\n" + "=" * 60)
    print(">>> 切分对比实验（200 字 vs 400 字块）")
    res = chunk_compare(qs)
    for sz, rows in res.items():
        print(f"\n[切分 {sz} 字]")
        for q, src, dist in rows:
            print(f"  Q: {q[:18]}…  → top1: {src}（距离 {dist}）")
