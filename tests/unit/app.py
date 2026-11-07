# app.py

# 1. 模拟：用户问题是否为空 (已有的功能)
def validate_question(question: str) -> bool:
    if not question or not question.strip():
        return False
    return True

# 2. 模拟：是否正确选择哲学视角
def select_philosophy_perspective(question: str) -> str:
    keywords = {
        "自由": "存在主义",
        "正义": "政治哲学",
        "存在": "形而上学"
    }
    for word, perspective in keywords.items():
        if word in question:
            return perspective
    return "其他哲学视角"

# 3. 模拟：是否正确生成 AI 提示词
def generate_ai_prompt(question: str, perspective: str) -> str:
    if not question or not perspective:
        return ""
    return f"你是一位{perspective}哲学家，请回答以下问题：{question}"

# 4. 模拟：是否正确处理历史对话
def process_conversation_history(history: list[str]) -> str:
    # 只提取人类的问题，过滤掉 AI 的回答
    return "\n".join(history[::2]) if history else ""

# 5. 模拟：是否正确整理最终总结
def format_final_summary(raw_text: str) -> str:
    return f"## 总结\n\n{raw_text.strip()}"

# app.py

# 6. 新增功能：将摄氏度转换为华氏度
def celsius_to_fahrenheit(celsius: float) -> float:
    """将摄氏度转换为华氏度"""
    return (celsius * 9 / 5) + 32

# 7. 新增功能：获取列表中的最大值
def get_max_value(numbers: list) -> float:
    """获取列表中的最大值，若列表为空则抛出 ValueError"""
    if not numbers:
        raise ValueError("列表不能为空")
    return max(numbers)

# app.py 文件末尾追加以下代码

# 8. 集成功能：完整的 AI 提示词生成流水线
def create_ai_prompt_pipeline(question: str) -> str:
    """
    模拟完整的流水线：
    1. 校验问题
    2. 选择哲学视角
    3. 生成最终提示词
    """
    # 校验输入
    if not validate_question(question):
        return "错误：请输入有效问题"
    
    # 模块间协作：使用 select_philosophy_perspective 的结果
    perspective = select_philosophy_perspective(question)
    
    # 模块间协作：将结果传入 generate_ai_prompt
    final_prompt = generate_ai_prompt(question, perspective)
    
    return final_prompt