会议分析平台 - Trae Builder专用Markdown需求文档

【构建模块】角色设定

你是一位资深 Python 全栈工程师，擅长使用 Gradio 构建本地 AI 应用。

【构建模块】任务目标

基于以下需求文档，构建一个本地部署的交互式会议分析平台。技术栈：Python 3.9+, Gradio 4.x, OpenAI Python SDK (对接 Qwen 3.5 Plus API)。

【构建模块】1. 核心架构要求

1. 运行环境：本地部署，前端界面本地运行，LLM 推理通过 API 调用。默认运行端口：7860（Gradio 默认端口，可修改，对应.env中GRADIO_PORT参数），默认服务器地址：0.0.0.0（支持本地局域网访问，对应.env中GRADIO_SERVER_NAME参数）；Python 版本要求 ≥3.9（贴合任务目标技术栈要求）。
2. LLM 接口：使用 OpenAI 兼容接口对接 Qwen 3.5 Plus。
   - Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1
   - Model: qwen3.5-plus (默认指定)
   - 库：openai Python 官方库
   - 默认参数：temperature=0.7（平衡回答准确性与灵活性，对应.env中LLM_TEMPERATURE参数），max_tokens=2048（满足会议报告生成及多轮对话需求，对应.env中LLM_MAX_TOKENS参数），stream=True（默认开启流式输出，贴合界面流式展示需求）。
3. 隐私安全：API Key 通过 .env 文件管理，严禁硬编码在代码中。用户上传的.txt文件保存至uploads/文件夹临时存储，文件内容仅存于内存，关闭网页即清除；默认不保留历史会话文件，关闭应用后uploads/文件夹内文件可手动清理（不自动删除，避免误删用户上传文件）；演示用预设会议纪要文件存于demo_docs/文件夹，仅开放读取权限，禁止用户通过网页修改/删除该文件夹内文件。
4. 会话管理：支持多会话并行。每个上传的文件或加载的演示文件对应一个独立的会话窗口（类似 ChatGPT 的左侧gr.List会话列表 + 右侧对话区），各会话互不干扰；默认会话无数量限制（贴合本地部署轻量需求），会话ID采用UUID自动生成（默认无过期时间），无需手动配置。
5. 演示文件加载：新增演示用会议纪要库功能，用于demo演示时快速加载文件，无需本地上传；预设演示文件存于项目根目录demo_docs/文件夹（自动创建），用户可在网页端直接选择加载，加载后生成独立会话，与用户上传文件的会话逻辑完全一致。

【构建模块】2. 核心逻辑流

1. 用户启动应用，看到空白对话区、左侧gr.List会话列表，以及演示文件加载入口。
2. 用户可选择两种方式获取会议纪要：① 上传 .txt 文件；② 从演示会议纪要库中选择预设文件。
3. 方式一（上传文件）：系统创建新会话 ID，将上传的.txt文件保存至项目根目录uploads/文件夹（默认存储位置），读取文件内容，初始化该新会话的聊天历史（为空，不影响任何已有会话）。
4. 方式二（加载演示文件）：系统创建新会话 ID，读取demo_docs/文件夹内选中的预设.txt文件内容（不保存至uploads/，避免混淆），初始化该新会话的聊天历史（为空，不影响任何已有会话）。
5. 两种方式后续流程一致：调用 Qwen API 生成初始结构化报告。
6. 将报告作为第一条 AI 消息插入该新会话的聊天历史。
7. 左侧gr.List会话列表新增该文件条目（演示文件条目前加“📋 演示文件：”标识，区分用户上传文件），并自动切换到该新会话。
8. 用户提问时，系统仅结合当前选中会话的文件内容 + 该会话的历史对话，调用 Qwen API 生成回答。
9. 支持流式输出（Stream）以提升体验。
10. 点击左侧gr.List会话列表中的历史会话，可切换回之前的文件对话上下文，所有会话的聊天历史均保持独立、不被篡改。

【构建模块】3. 功能需求详情

1. 会话创建机制：
   - 触发器：两种触发方式，① gr.File 组件的 change 事件（用户上传文件）；② 演示文件加载组件的点击/选择事件（用户加载预设演示文件）。
   - 行为：两种方式均生成唯一 Session ID，将 {filename, file_content, chat_history, file_type} 存入全局状态字典（chat_history 初始为空，仅属于该新会话；file_type区分“user_upload”（用户上传）和“demo”（演示文件）），不修改任何已有会话数据；其中，用户上传文件需保存至项目根目录uploads/文件夹（默认存储位置），演示文件仅读取demo_docs/文件夹内内容，不保存至uploads/。
   - 界面：左侧会话列表更新，演示文件条目前加“📋 演示文件：”标识，主对话区切换为新会话。
2. 交互式分析流程：
   - 初始报告结构：必须包含 ## 会议基本信息，## 会议核心主题/议程回顾，## 决策/共识，## 待办事项，## 风险/问题，## 后续建议 六个核心模块，使用 ✅⚠️ 图标；其中待办事项需明确待办内容、责任人、截止时间，贴合职场会议总结实际场景。
   - 多轮对话：System Prompt 必须注入当前会话的原始会议纪要内容（用户上传文件对应uploads/内原始文本，演示文件对应demo_docs/内原始文本，均未加工，确保AI对话不脱离当前会议）。
   - Prompt规范：需封装2类核心Prompt（均在core/analyzer.py中实现），确保Trae生成完整：① 初始报告Prompt（用于生成上述6模块结构化报告，要求语言简洁、逻辑清晰，贴合职场会议总结风格）；② 多轮对话Prompt（用于用户提问时，结合原始会议纪要+会话历史，生成精准、不编造的回答，禁止脱离文件内容）。
   - 上下文永续：切换会话时，完整恢复该会话的聊天历史和文件上下文，其他会话的历史数据保持不变。
3. 界面 UI 规范 (Gradio Blocks)：
   - 布局：左右分栏。
     - 左侧 (Sidebar)：会话列表（使用gr.List组件），垂直展示所有会话的文件名（演示文件标注“📋 演示文件：”），支持点击切换，当前选中会话需自定义高亮样式（与常用大模型网页端布局一致）；会话列表旁新增演示文件加载入口（使用gr.Dropdown组件，显示demo_docs/内所有.txt文件名，支持选择加载）。
     - 右侧 (Main)：顶部状态栏（显示当前基于哪个文件，标注“演示文件”或“用户上传文件”），中间 gr.Chatbot (气泡式布局)，启动网页时Chatbot右侧显示欢迎语：“上传会议纪要或加载演示文件，一键生成分析报告～”；底部 gr.Textbox + gr.Button（Textbox 可设置默认提示文字，如“请输入你的问题，例如：提取会议待办事项”）。
   - 样式：使用 gr.themes.Soft()，报告部分使用 Markdown 渲染；会话列表选中项高亮样式需明确（如背景色加深、边框加粗），与未选中项区分明显。
   - 错误处理：若 API 调用失败，在聊天区显示红色错误提示，不崩溃；若demo_docs/文件夹为空，加载入口提示“无演示文件，请放入.txt文件至demo_docs/文件夹”；文件上传/加载时，若格式非.txt或大小超过10MB，提示“仅支持≤10MB的.txt文件，请重新选择”。

【构建模块】4. 文件结构要求

```
meeting_analyzer/
├── app.py              # 主启动文件 (Gradio 入口，包含会话管理逻辑、演示文件加载逻辑、文件校验逻辑)
├── core/
│   ├── llm_client.py   # 封装 OpenAI SDK 调用 Qwen API，包含异常捕获
│   ├── analyzer.py     # 封装 Prompt 模板和初始报告生成逻辑
│   └── config.py       # 配置项，统一读取.env环境变量（API Base URL, Model Name、所有默认参数）
├── .env                # 环境变量 (DASHSCOPE_API_KEY=...)
├── .env.example        # 环境变量示例（包含所有默认参数，供用户参考配置）
├── requirements.txt    # 依赖列表（含Python版本约束）
├── README.md           # 启动说明（含API Key获取、参数修改、依赖安装、启动命令、demo_docs使用方法）
├── uploads/            # 用户上传的原始会议.txt文件默认存储位置，自动创建，仅用于临时存储上传文件
└── demo_docs/          # 演示用预设会议纪要库，自动创建，用于存放demo演示的.txt文件，仅开放读取权限
```

【构建模块】5. 关键代码逻辑指引

【依赖模块】需先完成core/config.py的环境变量读取逻辑，再实现llm_client.py和app.py的代码。

1. 环境变量配置 (.env)：
```
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
QWEN_MODEL_NAME=qwen3.5-plus
API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# 新增默认参数环境变量（可手动修改，对应核心架构及功能需求中的默认参数）
GRADIO_PORT=7860          # Gradio 应用默认运行端口（对应运行环境默认端口）
GRADIO_SERVER_NAME=0.0.0.0 # 默认服务器地址，支持本地局域网访问（对应运行环境默认地址）
LLM_TEMPERATURE=0.7       # LLM 生成回答的温度系数（对应LLM接口默认参数）
LLM_MAX_TOKENS=2048       # LLM 单次回答最大 tokens 限制（对应LLM接口默认参数）
```

2. 会话状态管理 (app.py)：
   - 使用 gr.State 存储一个字典：sessions = {session_id: {"filename": str, "content": str, "history": list, "file_type": str}} # file_type区分“user_upload”（用户上传）和“demo”（演示文件）
   - 使用 gr.State 存储当前选中的 session_id。
   - 上传文件时：生成新 UUID 作为 session_id，将用户上传的.txt文件保存至项目根目录的uploads/文件夹（默认存储位置），读取文件内容初始化该新 session 数据（chat_history 为空，file_type="user_upload"），更新 sessions 字典，更新 current_session_id，不操作任何已有 session；同时更新左侧gr.List会话列表，将新会话（文件名）追加到列表末尾，并自动选中该会话。
   - 加载演示文件时：生成新 UUID 作为 session_id，读取demo_docs/文件夹内选中的.txt文件内容（不保存至uploads/），初始化该新 session 数据（chat_history 为空，file_type="demo"），更新 sessions 字典，更新 current_session_id，不操作任何已有 session；同时更新左侧gr.List会话列表，将新会话（标注“📋 演示文件：”+文件名）追加到列表末尾，并自动选中该会话。
   - 切换会话时：点击左侧gr.List中的会话条目，根据对应的session_id从 sessions 字典读取 history、filename 和 file_type，刷新 Chatbot 和状态栏（标注文件类型）。
   - 发送消息时：根据 current_session_id 更新该会话的 history，不影响其他会话，左侧gr.List中的会话条目无需变动。
   - 默认参数：Gradio 应用默认端口7860、默认服务器地址0.0.0.0（均从.env读取，无配置则用默认值）；会话无数量限制，session_id 采用UUID自动生成，无过期时间（贴合会话管理默认参数要求）；demo_docs/和uploads/文件夹自动创建（若不存在），仅读取demo_docs/文件夹内.txt文件。
   - 补充逻辑：需实现文件校验逻辑（上传/加载时，校验文件格式为.txt、大小≤10MB），校验失败则提示用户，不创建会话。

3. LLM 客户端封装 (core/llm_client.py)：
   - 使用 openai.OpenAI 类，初始化时传入 api_key 和 base_url。
   - 实现 chat_with_qwen 函数，支持 stream=True（默认开启，贴合流式输出需求）；函数需接收 session 中的 file_content、历史对话，结合 Prompt 模板生成请求参数。
   - 包含 try-except 块捕获 API 异常（如API Key错误、网络异常、模型调用失败等），捕获异常后返回可在Gradio界面显示的友好提示。
   - 默认参数：temperature=0.7（从环境变量读取，默认0.7），max_tokens=2048（从环境变量读取，默认2048），stream=True（默认开启，贴合流式输出需求），与LLM接口默认参数完全一致。

4. Prompt封装 (core/analyzer.py)：
   - 初始报告Prompt：模板需明确要求AI输出包含## 会议基本信息等6个核心模块，使用✅⚠️图标，待办事项明确责任人、截止时间，语言简洁、贴合职场风格，仅基于当前会话的原始会议纪要（用户上传/演示文件）生成，不编造信息。
   - 多轮对话Prompt：模板需包含System Prompt（注入当前会话原始会议纪要）和MessagesPlaceholder（关联会话历史），要求AI仅结合原始纪要和历史对话回答，不脱离文件内容、不编造信息，回答简洁精准。
   - 默认参数：初始报告生成默认语言为中文，回答格式为Markdown（贴合界面渲染需求）；多轮对话默认不保留超过10轮的历史上下文（避免tokens溢出，可修改），与多轮对话功能需求一致。

5. 依赖库 (requirements.txt)：
```
gradio>=4.0.0
openai>=1.0.0
python-dotenv
uuid
os # 新增，用于读取demo_docs/和uploads/文件夹内文件、路径操作
uuid # 用于生成唯一session_id（已提及，保留确保无遗漏）
```

【构建模块】6. 验收标准

1. 配置检查：代码启动时检测 .env 文件，若缺失 API Key 则提示用户创建；同时检测.env中默认参数（端口、LLM参数等），若未配置则使用默认值；自动创建uploads/和demo_docs/文件夹（若不存在）；检测Python版本≥3.9，若版本过低则提示升级；core/config.py 可正常读取所有环境变量，参数配置统一。
2. 多会话测试：上传文件 A，生成报告；加载演示文件 B，生成报告。点击左侧gr.List会话列表切换 A/B，对话历史互不干扰，均完整保留（符合“默认会话无数量限制、会话ID自动生成”的参数要求）；会话列表中演示文件有明确标识，与用户上传文件区分清晰。
3. 上下文测试：在文件 A 会话中追问，AI 仅引用文件 A 内容；切换到演示文件 B 后，AI 仅引用文件 B 内容（符合多轮对话Prompt参数要求）；多轮对话超过10轮时，自动丢弃最早的历史上下文，避免tokens溢出。
4. 异常处理：API Key 错误、网络异常、模型调用失败时，界面显示友好红色提示，不抛出 Python traceback；demo_docs/文件夹为空时，加载入口有明确提示，不崩溃；文件上传/加载时，格式非.txt或大小超过10MB，提示用户重新选择，不创建会话。
5. 流式输出：AI 回答时文字逐字显示，无明显卡顿（符合stream=True默认参数要求）。
6. 模型确认：默认调用 qwen3.5-plus 模型；LLM 生成参数（temperature=0.7、max_tokens=2048）默认生效，修改.env文件后参数可正常生效。
7. 默认参数校验：所有默认参数（端口、LLM参数、会话参数等）可通过.env文件修改，无需改动代码；uploads/和demo_docs/文件夹自动创建，文件存储/读取符合隐私安全参数要求；Gradio端口修改后，应用可正常启动并通过新端口访问。
8. 演示文件加载测试：选择demo_docs/内的.txt文件，可快速创建会话、生成报告，加载逻辑与上传文件一致，无数据混淆；演示文件仅可读取，无法通过网页修改/删除。
9. 界面测试：左侧gr.List会话列表选中项高亮明显，演示文件标识清晰；Textbox 有默认提示文字，布局合理；报告通过Markdown渲染，格式清晰；所有组件交互流畅，无卡顿、无布局错乱。
10. 代码可运行性：所有路径引用正确，安装依赖后（pip install -r requirements.txt），执行启动命令可正常启动应用；core/config.py 可正常调用环境变量，无参数缺失。

【构建模块】7. 额外指令（必须严格遵守）

【优先实现】请优先生成 app.py 和 core/llm_client.py 的完整代码，同步完善core/analyzer.py中的Prompt模板（初始报告Prompt和多轮对话Prompt），新增演示文件加载相关逻辑、文件校验逻辑。
1. 确保 openai 库的版本兼容 DashScope 的兼容模式；确保 Python 版本适配 ≥3.9（贴合技术栈要求）。
2. 界面需美观，左侧gr.List会话列表需清晰显示文件名（演示文件标注“📋 演示文件：”），当前选中项需设置明显高亮样式（贴合大模型网页端，如背景色加深、边框加粗），间距适中、字体清晰；演示文件加载入口（gr.Dropdown组件）布局合理，与会话列表适配；Textbox 可设置默认提示文字，提升用户体验。
3. 在 README 中写明如何获取 Qwen API Key 的步骤，同时说明所有默认参数（端口、LLM参数、会话参数等）的含义及修改方法；补充demo_docs/文件夹的用途、使用方法（可放入演示用.txt文件）；补充Python版本要求、依赖库安装命令（pip install -r requirements.txt）、应用启动命令（如python app.py）。
4. 移除所有 Mermaid 图表，使用纯文字描述逻辑。
5. 确保代码中所有路径引用正确，可直接运行；用户上传的.txt文件默认存储在项目根目录的uploads/文件夹，演示文件存于demo_docs/文件夹，代码需自动创建两个文件夹（若不存在），避免路径报错；演示文件仅读取，不修改、不保存至uploads/。
6. 注意 Gradio 的状态管理陷阱，确保多会话切换时数据不串扰、不覆盖；默认会话无数量限制，session_id 采用UUID自动生成，无过期时间；需区分用户上传文件和演示文件的会话数据，不混淆。
7. 上传文件和演示文件加载时均增加校验：仅支持 .txt 格式，文件大小建议 ≤10MB；demo_docs/文件夹为空时，加载入口提示“无演示文件，请放入.txt文件至demo_docs/文件夹”；文件校验失败时，显示友好提示，不创建会话、不崩溃。
8. 流式输出必须使用 Gradio 的 generator 生成器，逐字显示（默认开启stream=True），无明显卡顿。
9. 启动时自动检查目录结构，自动生成 .env.example 文件（包含所有默认参数环境变量），同时自动创建uploads/和demo_docs/文件夹（分别对应用户上传文件和演示文件存储/读取位置）；检测到.env文件缺失API Key时，提示用户配置。
10. Prompt模板需严格贴合需求，确保初始报告生成符合6模块要求，多轮对话不脱离原始会议纪要内容（用户上传/演示文件），无编造信息；初始报告默认中文、Markdown格式，多轮对话默认保留10轮内历史上下文。
11. 所有默认参数需支持通过.env文件修改（如端口、LLM温度系数等），无需修改代码即可调整，提升灵活性。
12. 演示文件加载逻辑需与用户上传文件逻辑兼容，共用会话管理、LLM调用、Prompt模板等核心逻辑，不重复开发。
13. core/config.py 需实现环境变量读取逻辑，统一管理API Base URL、Model Name、所有默认参数，供app.py、llm_client.py调用，避免参数分散配置。
