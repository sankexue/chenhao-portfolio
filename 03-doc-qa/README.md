# 智能文档问答工具

> 项目类型：**AI 应用工程实践**（非数据分析项目）。用于练习 API 调用、文档解析与会话状态管理。

上传 PDF / Word / TXT，让大模型基于**文档内容**回答问题。用于快速检索长文档中的信息，避免翻页查找。

## 功能

- 支持 PDF（PyPDF2）、Word（python-docx）、TXT 三种格式
- 提取正文后作为 system prompt 注入，让模型只依据文档作答
- 多轮对话：历史问答一并传给模型，保证上下文连续
- 会话清空、对话记录导出为 JSON

## 技术栈

Python · Streamlit · DeepSeek Chat API · PyPDF2 · python-docx

## 本地运行

```bash
pip install streamlit requests PyPDF2 python-docx
$env:DEEPSEEK_API_KEY="你的key"     # PowerShell
streamlit run app.py
```

打开 http://localhost:8501 ，上传文件后即可提问。

## 关键实现

```python
# 把文档正文作为 system prompt 注入，约束模型不要编造
st.session_state.messages = [
    {"role": "system", "content": f"请根据以下内容回答用户的问题，不要编造答案：\n\n{content}"}
]

response = requests.post(url, headers=headers, json=data)
reply = response.json()["choices"][0]["message"]["content"]
```

## 踩过的坑

1. **Word 表格文字重复提取**：`doc.tables` 遍历单元格时，合并单元格会被重复读到，需用 `seen_cells` 去重
2. **PDF 表格错行**：`PyPDF2` 提取表格页时行列错位，长文本需要按行拆分清洗
3. **API Key 管理**：早期版本把 key 硬编码在代码里，已改为读取环境变量

## 目录结构

```
03-智能文档问答/
├── README.md
├── app.py
└── requirements.txt
```

> 注意：本项目不含任何真实 API Key，运行前请自行配置环境变量。
