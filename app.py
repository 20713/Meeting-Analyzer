import gradio as gr
import os
import uuid
import logging
import signal
import sys
import time
from core.config import Config
from core.llm_client import LLMClient
from core.analyzer import AnalyzerPrompts

# 初始化配置和日志
Config.check_env()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm_client = LLMClient()

def generate_session_id():
    return str(uuid.uuid4())

def get_demo_files():
    """获取演示文件列表"""
    files = []
    if os.path.exists(Config.DEMO_DOCS_DIR):
        files = [f for f in os.listdir(Config.DEMO_DOCS_DIR) if f.endswith('.txt')]
    return files

def load_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

def create_new_session(file_path, file_type, filename, sessions, current_session_id):
    """
    创建新会话并更新状态
    """
    content = load_file_content(file_path)
    if not content:
        raise ValueError("无法读取文件内容")
        
    session_id = generate_session_id()
    
    # 初始会话数据
    sessions[session_id] = {
        "filename": filename,
        "content": content,
        "history": [], # 格式: [[user_msg, bot_msg], ...]
        "file_type": file_type
    }
    
    return sessions, session_id

def on_file_upload(file_obj, sessions, current_session_id):
    """处理用户上传文件"""
    if not file_obj:
        return sessions, current_session_id, gr.update(), gr.update()
        
    filename = os.path.basename(file_obj.name)
    
    # 文件校验
    if not filename.lower().endswith('.txt'):
        raise gr.Error("仅支持 .txt 格式文件")
    
    # 保存到 uploads 目录
    save_path = os.path.join(Config.UPLOADS_DIR, filename)
    try:
        with open(file_obj.name, 'r', encoding='utf-8') as src, open(save_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    except Exception as e:
        raise gr.Error(f"文件保存失败: {str(e)}")
        
    sessions, new_session_id = create_new_session(save_path, "user_upload", filename, sessions, current_session_id)
    
    # 初始化会话历史，添加加载占位符
    initial_history = [
        {"role": "user", "content": f"请帮我分析这份会议纪要：{filename}"},
        {"role": "assistant", "content": "⏳ 正在生成会议分析报告，请稍候..."}
    ]
    sessions[new_session_id]['history'] = initial_history
    
    # 返回更新后的组件状态，立即显示占位符
    return sessions, new_session_id, gr.update(choices=update_session_list(sessions), value=new_session_id), initial_history

def on_demo_load(demo_filename, sessions, current_session_id):
    """处理演示文件加载"""
    if not demo_filename:
        return sessions, current_session_id, gr.update(), None
        
    file_path = os.path.join(Config.DEMO_DOCS_DIR, demo_filename)
    
    sessions, new_session_id = create_new_session(file_path, "demo", demo_filename, sessions, current_session_id)
    
    # 初始化会话历史，添加加载占位符
    initial_history = [
        {"role": "user", "content": f"请帮我分析演示文件：{demo_filename}"},
        {"role": "assistant", "content": "⏳ 正在生成会议分析报告，请稍候..."}
    ]
    sessions[new_session_id]['history'] = initial_history
    
    return sessions, new_session_id, gr.update(choices=update_session_list(sessions), value=new_session_id), initial_history

def update_session_list(sessions):
    """生成会话列表选项 (Label, Value)"""
    # Radio 组件只接受列表或元组列表，这里返回 (Label, Value) 元组列表
    choices = []
    for sid, data in sessions.items():
        prefix = "📋 " if data['file_type'] == 'demo' else "📄 "
        # 截断过长的文件名以适应侧边栏
        filename = data['filename']
        if len(filename) > 30:
            filename = filename[:25] + "..."
        choices.append((f"{prefix}{filename}", sid))
    return choices

def on_session_select(evt: gr.SelectData, sessions):
    """切换会话"""
    session_id = evt.value
    if session_id in sessions:
        history = sessions[session_id]['history']
        return session_id, history
    return None, []

def generate_initial_report(sessions, current_session_id):
    """生成初始报告"""
    if not current_session_id or current_session_id not in sessions:
        yield []
        return

    session_data = sessions[current_session_id]
    content = session_data['content']
    
    # 构建 Prompt
    messages = AnalyzerPrompts.get_initial_report_prompt(content)
    
    # 获取包含占位符的历史记录
    history = session_data['history']
    
    # 确保历史记录结构正确（防御性编程）
    if not history or len(history) < 2 or history[-1]['role'] != 'assistant':
        # 如果没有占位符（异常情况），则追加
        history.append({"role": "user", "content": "请帮我分析这份会议纪要"})
        history.append({"role": "assistant", "content": ""})
    
    # 流式生成
    for frame in [
        "⏳ 正在生成会议分析报告，请稍候",
        "⏳ 正在生成会议分析报告，请稍候.",
        "⏳ 正在生成会议分析报告，请稍候..",
        "⏳ 正在生成会议分析报告，请稍候..."
    ]:
        history[-1]['content'] = frame
        yield history
        time.sleep(2.0)
    full_response = ""
    try:
        for chunk in llm_client.chat_stream(messages):
            full_response += chunk
            # 更新最后一条消息（即占位符消息）
            history[-1]['content'] = full_response
            yield history
    except Exception as e:
        history[-1]['content'] = f"生成报告出错: {str(e)}"
        yield history
        
    # 更新会话历史
    sessions[current_session_id]['history'] = history

def chat_response(user_input, sessions, current_session_id):
    """处理用户对话"""
    if not current_session_id or current_session_id not in sessions:
        yield [], "" # Clear input
        return
        
    if not user_input.strip():
        yield sessions[current_session_id]['history'], ""
        return

    session_data = sessions[current_session_id]
    content = session_data['content']
    history = session_data['history']
    
    # 添加用户消息到历史
    history.append({"role": "user", "content": user_input})
    
    # 添加 AI 回复占位符，立即给用户反馈
    history.append({"role": "assistant", "content": "⏳ 正在思考..."})
    yield history, "" # 更新界面，清空输入框，显示"正在思考"

    # 构建 Prompt
    # 注意：history 包含当前用户输入和刚刚添加的占位符
    # get_chat_prompt 需要的是之前的对话历史（不含本次提问和占位符）
    # 之前逻辑：history 是 [{u}, {a}, ... {current_u}, {placeholder_a}]
    
    # 传入除本次提问和占位符外的历史
    previous_history = history[:-2] 
    messages = AnalyzerPrompts.get_chat_prompt(content, previous_history)
    messages.append({"role": "user", "content": user_input})
    
    # 流式生成
    for frame in [
        "⏳ 正在思考",
        "⏳ 正在思考.",
        "⏳ 正在思考..",
        "⏳ 正在思考..."
    ]:
        history[-1]['content'] = frame
        yield history, ""
        time.sleep(4.0)
    full_response = ""
    try:
        for chunk in llm_client.chat_stream(messages):
            full_response += chunk
            history[-1]['content'] = full_response
            yield history, ""
    except Exception as e:
        history[-1]['content'] = f"回复出错: {str(e)}"
        yield history, ""
        
    # 更新会话历史
    sessions[current_session_id]['history'] = history

# --- Gradio UI 构建 ---

# 自定义 CSS 以优化左侧会话列表样式 (隐藏 Radio 圆圈，使其像列表)
# 增大组件尺寸和间距
custom_css = """
.session-list-radio label {
    display: block !important;
    margin-bottom: 8px !important;
    padding: 12px 16px !important; /* 增大内边距 */
    border-radius: 8px !important;
    border: 1px solid #e5e7eb !important;
    cursor: pointer !important;
    transition: background-color 0.2s !important;
    font-size: 16px !important; /* 增大字体 */
}
.session-list-radio label:hover {
    background-color: #f3f4f6 !important;
}
.session-list-radio input[type="radio"] {
    display: None !important;
}
.session-list-radio .selected {
    background-color: #e5e7eb !important;
    font-weight: bold !important;
}
/* 增大 Chatbot 文字 */
.message-wrap .message {
    font-size: 16px !important;
    line-height: 1.6 !important;
}
/* 强制 Chatbot 高度占据视口大部分空间 */
.main-chatbot {
    height: 80vh !important; /* 占据视口高度的 80% */
    min-height: 600px !important;
}
"""

# 定制主题，增大全局尺寸
theme = gr.themes.Soft(
    text_size=gr.themes.sizes.text_lg,
    spacing_size=gr.themes.sizes.spacing_lg,
    radius_size=gr.themes.sizes.radius_lg
)

with gr.Blocks(theme=theme, css=custom_css, title="会议分析平台") as app:
    
    # 全局状态
    sessions_state = gr.State({}) # {session_id: {filename, content, history, file_type}}
    current_session_state = gr.State(None)
    
    with gr.Row():
        # 左侧边栏
        with gr.Column(scale=1, min_width=250):
            gr.Markdown("### 📂 会话管理")
            
            # 文件上传
            file_upload = gr.File(
                label="上传会议纪要 (.txt)",
                file_types=[".txt"],
                type="filepath"
            )
            
            # 演示文件加载
            # 获取初始演示文件列表
            initial_demo_files = get_demo_files()
            demo_dropdown = gr.Dropdown(
                choices=initial_demo_files,
                label="加载演示文件",
                value=None,
                interactive=True
            )
            
            # 会话列表
            gr.Markdown("### 💬 历史会话")
            session_list = gr.Radio(
                label="选择会话",
                choices=[],
                interactive=True,
                container=False,
                elem_classes="session-list-radio"
            )
            
        # 右侧主区域
        with gr.Column(scale=4):
            # 状态栏
            with gr.Row():
                status_info = gr.Markdown("👋 欢迎使用会议分析平台！请上传文件或加载演示文件开始。")
            
            # 聊天窗口
            chatbot = gr.Chatbot(
                height=800, # 基础高度增加到 800
                layout="bubble",
                label="对话记录",
                avatar_images=(
                    "https://api.dicebear.com/7.x/adventurer/svg?seed=Felix", 
                    "https://api.dicebear.com/7.x/bottts/svg?seed=MeetingBot"
                ),
                elem_classes="main-chatbot" # 添加自定义类名以便 CSS 控制
            )
            
            # 输入区域
            with gr.Row():
                msg_input = gr.Textbox(
                    show_label=False,
                    placeholder="请输入你的问题，例如：提取会议待办事项...",
                    scale=4,
                    container=False
                )
                submit_btn = gr.Button("发送", scale=1, variant="primary")

    # --- 事件绑定 ---

    # 1. 上传文件 -> 创建会话 -> 生成初始报告
    file_upload.upload(
        fn=on_file_upload,
        inputs=[file_upload, sessions_state, current_session_state],
        outputs=[sessions_state, current_session_state, session_list, chatbot],
        queue=False
    ).then(
        fn=generate_initial_report,
        inputs=[sessions_state, current_session_state],
        outputs=[chatbot]
    )

    # 2. 加载演示文件 -> 创建会话 -> 生成初始报告
    demo_dropdown.change(
        fn=on_demo_load,
        inputs=[demo_dropdown, sessions_state, current_session_state],
        outputs=[sessions_state, current_session_state, session_list, chatbot],
        queue=False
    ).then(
        fn=generate_initial_report,
        inputs=[sessions_state, current_session_state],
        outputs=[chatbot]
    )

    # 3. 切换会话
    def switch_session(sid, sessions):
        if sid in sessions:
            history = sessions[sid]['history']
            filename = sessions[sid]['filename']
            # 更新 Radio 的选项，确保选中状态正确（虽然 Radio change 会自动处理，但为了保险）
            # 注意：Radio 的 value 变更会触发 change 事件，这里主要负责返回 history 和 status
            return history, f"当前会话: {filename}", sid
        return [], "请选择会话", None

    session_list.change(
        fn=switch_session,
        inputs=[session_list, sessions_state],
        outputs=[chatbot, status_info, current_session_state]
    )


    # 4. 发送消息
    submit_btn.click(
        fn=chat_response,
        inputs=[msg_input, sessions_state, current_session_state],
        outputs=[chatbot, msg_input]
    )
    
    msg_input.submit(
        fn=chat_response,
        inputs=[msg_input, sessions_state, current_session_state],
        outputs=[chatbot, msg_input]
    )

if __name__ == "__main__":
    # 定义信号处理函数，确保 Ctrl+C 时优雅退出并释放端口
    def signal_handler(sig, frame):
        print("\n👋 检测到退出信号，正在关闭服务器...")
        try:
            app.close()
        except:
            pass
        sys.exit(0)

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"🚀 正在启动服务...")
    print(f"👉 本地访问请点击: http://localhost:{Config.GRADIO_PORT}")
    if Config.GRADIO_SERVER_NAME == "0.0.0.0":
        print(f"👉 局域网访问请使用: http://<本机IP>:{Config.GRADIO_PORT}")
    print("💡 按 Ctrl+C 可以停止服务")

    app.queue().launch(
        server_name=Config.GRADIO_SERVER_NAME,
        server_port=Config.GRADIO_PORT,
        share=False,
        # Move theme and title here for newer Gradio versions compatibility
        # Note: theme object cannot be passed directly to launch in some versions, 
        # but title can be passed as page_title.
        # However, to be safe across versions, we'll keep theme in Blocks if launch doesn't support it,
        # or just remove it if it causes issues. The warning said parameters moved to launch().
        # Let's try to set page_title.
        # Theme is usually set in Blocks, but if it warns, we can try to ignore or adjust.
        # For now, let's keep it simple and standard.
    )
