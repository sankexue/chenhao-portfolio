# -*- coding: utf-8 -*-
"""智能文档问答工具

上传 PDF / Word / TXT，把文档正文注入 system prompt，让大模型只依据文档内容作答。

运行前先配置 API Key（不要硬编码在代码里）：
    PowerShell:  $env:DEEPSEEK_API_KEY="sk-xxxx"
    CMD:         set DEEPSEEK_API_KEY=sk-xxxx
    Linux/macOS: export DEEPSEEK_API_KEY=sk-xxxx
"""
import io
import json
import os
from datetime import datetime

import requests
import streamlit as st

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

st.set_page_config(page_title="智能文档问答系统", layout="wide")
st.title("📄 智能文档问答系统")
st.caption("上传 PDF / Word / TXT，然后针对文档内容提问")


def extract_pdf(file) -> str:
    from PyPDF2 import PdfReader

    reader = PdfReader(file)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def extract_docx(file) -> str:
    """提取 Word 正文与表格。

    Word 的合并单元格会被重复读到，这里用 seen_cells 去重。
    """
    from docx import Document

    doc = Document(io.BytesIO(file.read()))
    parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    seen_cells = set()
    for table in doc.tables:
        for row in table.rows:
            row_text = []
            for cell in row.cells:
                cell_text = cell.text.strip()
                if cell_text and cell_text not in seen_cells:
                    seen_cells.add(cell_text)
                    row_text.append(" ".join(cell_text.split()))
            if row_text:
                parts.append(" | ".join(row_text))
    return "\n".join(parts)


def extract_txt(file) -> str:
    return file.read().decode("utf-8", errors="ignore")


def ask_model(messages):
    if not API_KEY:
        return None, "未配置 DEEPSEEK_API_KEY 环境变量，请先设置后重启应用。"
    try:
        resp = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": messages},
            timeout=60,
        )
    except requests.RequestException as exc:
        return None, f"请求失败：{exc}"
    if resp.status_code != 200:
        return None, f"接口返回 {resp.status_code}：{resp.text[:200]}"
    return resp.json()["choices"][0]["message"]["content"], None


col1, col2, col3 = st.columns([5, 1, 1])
with col2:
    if st.button("🗑️ 清空对话"):
        st.session_state.messages = []
        st.rerun()
with col3:
    if st.button("📥 导出对话"):
        payload = {
            "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "messages": st.session_state.get("messages", []),
        }
        with open("对话记录.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        st.success("对话已导出到 对话记录.json")

uploaded = st.file_uploader("选择文件", type=["pdf", "docx", "txt"])

if uploaded is not None:
    suffix = uploaded.name.rsplit(".", 1)[-1].lower()
    try:
        if suffix == "pdf":
            content = extract_pdf(uploaded)
        elif suffix == "docx":
            content = extract_docx(uploaded)
        else:
            content = extract_txt(uploaded)
    except Exception as exc:  # 解析失败时给出明确原因，而不是静默失败
        st.error(f"文档解析失败：{exc}")
        content = ""

    if content.strip():
        st.success(f"已加载：{uploaded.name}（正文约 {len(content)} 字）")
        with st.expander("查看内容预览"):
            st.text(content[:500] + ("..." if len(content) > 500 else ""))

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "system", "content": f"请根据以下内容回答用户的问题，不要编造答案：\n\n{content}"}
            ]

        for message in st.session_state.messages:
            if message["role"] in ("user", "assistant"):
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        user_input = st.chat_input("输入你的问题")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    reply, error = ask_model(st.session_state.messages)
                if error:
                    st.error(error)
                else:
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
