"""
Day13: 把 Day12 的 RAG 升级成"可反复对话的本地知识库助手"
在 rag.py 基础上新增两项生产级能力：
  ① 索引持久化：首次建索引后存盘，之后启动直接加载（按知识库文件修改时间判断是否需要重建）
  ② 交互式问答：命令行循环输入问题，输入 exit/quit 退出
复用 rag.py 的 chunk_text / build_index / retrieve / answer / get_embedder，不改动原文件。
"""
import os
import pickle
from rag import chunk_text, build_index, answer

HERE = os.path.dirname(__file__)
KB_PATH = os.path.join(HERE, "kb_compliance.txt")
CACHE_FILE = os.path.join(HERE, "kb_index.cache")


def load_kb_cached(kb_path=KB_PATH, cache_file=CACHE_FILE, force=False):
    """加载知识库索引。缓存有效则直接读盘，否则重建并存盘。"""
    # 缓存有效条件：cache 存在、非强制、且 cache 比知识库新（知识库没改过）
    cache_valid = (
        not force
        and os.path.exists(cache_file)
        and os.path.getmtime(cache_file) >= os.path.getmtime(kb_path)
    )
    if cache_valid:
        with open(cache_file, "rb") as f:
            chunks, index = pickle.load(f)
        print(f"[缓存] 直接加载索引：{len(chunks)} 块（秒级）")
        return chunks, index

    # 否则重建：读文本 → 切分 → 本地 bge 向量化 → 存盘
    with open(kb_path, encoding="utf-8") as f:
        text = f.read()
    chunks = chunk_text(text)
    index = build_index(chunks)
    with open(cache_file, "wb") as f:
        pickle.dump((chunks, index), f)
    print(f"[重建] 知识库切分 {len(chunks)} 块，索引已存盘：{cache_file}")
    return chunks, index


def chat_loop(chunks, index):
    """命令行交互问答：输入问题回车得答案，exit/quit/退出 结束。"""
    print("\n=== 本地合规助手（输入 exit/quit 退出）===")
    while True:
        try:
            q = input("你问：").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            continue
        if q.lower() in ("exit", "quit", "退出"):
            print("再见")
            break
        print("答：", answer(q, chunks, index), "\n")


if __name__ == "__main__":
    chunks, index = load_kb_cached()
    chat_loop(chunks, index)
