class AnalyzerPrompts:
    """Helper class to manage prompts for the meeting analyzer."""
    
    @staticmethod
    def get_initial_report_prompt(meeting_content):
        """
        Generate the prompt for the initial meeting analysis report.
        
        Args:
            meeting_content (str): The raw text of the meeting minutes.
            
        Returns:
            list: The message list for the LLM.
        """
        system_prompt = (
            "你是一位资深会议分析师。你的任务是根据提供的会议纪要，生成一份结构清晰、重点突出的Markdown格式分析报告。"
            "报告语言需简洁、专业，贴合职场风格。"
        )
        
        user_prompt = f"""请对以下会议纪要进行深入分析，并严格按照以下结构生成报告：

1. ## 会议基本信息
   - 提取会议时间、地点、参会人员、主持人等基础信息。

2. ## 会议核心主题/议程回顾
   - 简要概括会议讨论的主要议题和流程。

3. ## 决策/共识 ✅
   - 列出会议达成的关键决策和共识，使用 ✅ 图标标记。

4. ## 待办事项 ⚠️
   - 提取所有待办任务，明确责任人、截止时间（如有）。
   - 格式示例：- [责任人] 任务描述 (截止日期: YYYY-MM-DD)

5. ## 风险/问题
   - 指出会议中提到的潜在风险、未解决问题或痛点。

6. ## 后续建议
   - 基于会议内容，提出下一步的行动建议或改进方向。

---
**会议纪要原文：**
{meeting_content}
"""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    @staticmethod
    def get_chat_prompt(meeting_content, chat_history):
        """
        Generate the prompt for follow-up questions based on meeting content and chat history.
        
        Args:
            meeting_content (str): The raw text of the meeting minutes.
            chat_history (list): List of message dictionaries [{"role": "user/assistant", "content": "..."}].
            
        Returns:
            list: The message list for the LLM.
        """
        # System prompt injecting the meeting context
        system_message = {
            "role": "system", 
            "content": f"""你是一位智能会议助手。请基于以下提供的会议纪要原文回答用户的问题。
            
**原则：**
1. 答案必须严格基于会议纪要内容，不得编造信息。
2. 如果会议纪要中没有相关信息，请明确告知用户“文件中未提及相关内容”。
3. 回答需简洁、准确。

**会议纪要原文：**
{meeting_content}
"""
        }
        
        messages = [system_message]
        
        # Append recent chat history (limit to last 10 messages to save tokens)
        # chat_history format is [{"role": "user", "content": "..."}, ...]
        recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
        
        for msg in recent_history:
            if msg.get('content'): # Ensure content is not empty/None
                messages.append({"role": msg['role'], "content": msg['content']})
                
        return messages
