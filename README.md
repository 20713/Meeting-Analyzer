# 会议分析平台 (Meeting Analyzer)

这是一个基于本地部署的交互式会议分析平台，利用 Qwen 3.5 Plus 大模型帮助用户快速分析会议纪要，提取待办事项、决策点和风险，并支持多轮对话。

## ✨ 核心功能

*   **智能分析报告**：自动生成包含会议主题、决策共识、待办事项（含责任人/截止时间）、风险及建议的结构化 Markdown 报告。
*   **交互式对话**：基于当前会议纪要内容进行多轮问答，支持流式输出。
*   **多会话管理**：支持同时上传多个文件，独立管理会话上下文，互不干扰。
*   **演示模式**：内置演示文件库，无需上传即可快速体验功能。
*   **隐私安全**：用户上传文件仅临时存储，演示文件只读，API Key 本地管理。

## 🛠️ 技术栈

*   **语言**: Python 3.9+
*   **界面**: Gradio 4.x
*   **模型**: Qwen 3.5 Plus (via OpenAI Compatible API)

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.9 或更高版本。

```bash
# 克隆或下载项目代码
git clone <repository_url>
cd meeting_analyzer
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制示例配置文件并重命名为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 DashScope API Key：

```ini
DASHSCOPE_API_KEY=sk-your-api-key-here
```

**可选配置项**：
*   `GRADIO_PORT`: 应用运行端口（默认 7860）
*   `LLM_TEMPERATURE`: 模型温度系数（默认 0.7）
*   `LLM_MAX_TOKENS`: 单次回答最大 Token 数（默认 2048）

### 4. 启动应用

```bash
python app.py
```

启动成功后，浏览器访问终端显示的地址（通常为 `http://localhost:7860`）。

## 📂 目录结构

```
meeting_analyzer/
├── app.py              # 主启动文件
├── core/
│   ├── config.py       # 配置管理
│   ├── llm_client.py   # LLM 客户端封装
│   └── analyzer.py     # Prompt 管理
├── uploads/            # 用户上传文件临时存储 (自动创建)
├── demo_docs/          # 演示文件库 (自动创建)
├── .env                # 环境变量配置 (需手动创建)
└── requirements.txt    # 项目依赖
```

## 📝 使用指南

1.  **上传/加载文件**：
    *   点击左侧“上传会议纪要”按钮上传本地 `.txt` 文件。
    *   或在“加载演示文件”下拉框中选择预设文件。
2.  **查看报告**：
    *   文件加载后，系统会自动生成一份结构化的分析报告。
3.  **多轮对话**：
    *   在底部输入框输入问题（如“李四负责什么任务？”），系统将基于当前文件内容回答。
4.  **切换会话**：
    *   通过左侧“选择会话”下拉框在不同文件间切换，对话历史会自动恢复。

## ⚠️ 注意事项

*   仅支持 `.txt` 格式的文本文件。
*   请确保 `.env` 文件中的 API Key 有效且有足够的额度。
*   `demo_docs/` 文件夹内的文件仅供读取，不可通过网页修改。
