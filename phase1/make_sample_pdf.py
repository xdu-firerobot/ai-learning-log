"""make_sample_pdf.py —— 造一个中文测试 PDF，用于验证 RAG 的 PDF 解析能力。
字体用 Windows 自带黑体 SimHei。生成 phase1/sample_policy.pdf。
（仅演示用，内容为虚构的"小贷监管办法"样例条款，非真实法规）"""
import os
from fpdf import FPDF

BASE = os.path.dirname(os.path.abspath(__file__))
FONT = "C:/Windows/Fonts/simhei.ttf"


class PDF(FPDF):
    def header(self):
        self.set_font("SimHei", "", 13)
        self.cell(0, 10, "小额贷款公司监督管理暂行办法（样例摘录）", align="C")
        self.ln(12)


def main():
    pdf = PDF()
    pdf.add_font("SimHei", "", FONT)
    pdf.add_page()
    pdf.set_font("SimHei", "", 11)
    body = (
        "第一条 小额贷款公司开展营销宣传，应当明示贷款主体、年化综合费率及风险提示，"
        "不得含有“保本保收益”“无风险”“零门槛”等误导性表述。\n\n"
        "第二条 贷款营销短信须包含清晰可辨的风险提示语句，例如："
        "“借贷有风险，理性消费，按时还款，避免逾期影响征信。”"
        "不得以隐藏链接、极小字号等方式弱化风险提示。\n\n"
        "第三条 小额贷款公司不得以收取“会员费”“服务费”等名目变相提高"
        "综合融资成本；综合融资成本不得超过司法机关规定的利率保护上限。"
    )
    pdf.multi_cell(0, 8, body)
    out = os.path.join(BASE, "sample_policy.pdf")
    pdf.output(out)
    print("已生成:", out)


if __name__ == "__main__":
    main()
