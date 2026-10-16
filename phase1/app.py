import streamlit as st
import policy_kb as kb

st.title("小贷政策知识库问答")

@st.cache_resource                 # 只建一次索引，刷新不重建
def get_coll():
    coll, total, added = kb.build_incremental()
    return coll

coll = get_coll()

q = st.text_input("输入你的问题：")
if q:
    with st.spinner("检索中..."):
        ans = kb.answer(q, coll, stream=False)   # 网页里先用非流式
    st.write(ans)
