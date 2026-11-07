# test_app.py
from app import (
    validate_question,
    select_philosophy_perspective,
    generate_ai_prompt,
    process_conversation_history,
    format_final_summary
)

# --- 测试 1: 用户问题是否为空 ---
def test_validate_question():
    assert validate_question("你好") is True
    assert validate_question("") is False
    assert validate_question("   ") is False

# --- 测试 2: 是否正确选择哲学视角 ---
def test_select_philosophy_perspective():
    assert select_philosophy_perspective("我们是否拥有自由？") == "存在主义"
    assert select_philosophy_perspective("什么是正义？") == "政治哲学"
    assert select_philosophy_perspective("今天天气怎么样") == "其他哲学视角"

# --- 测试 3: 是否正确生成 AI 提示词 ---
def test_generate_ai_prompt():
    prompt = generate_ai_prompt("人为什么活着？", "存在主义")
    assert "存在主义" in prompt and "人为什么活着？" in prompt
    assert generate_ai_prompt("", "存在主义") == ""

# --- 测试 4: 是否正确处理历史对话 ---
def test_process_conversation_history():
    history = ["你好", "你好，我是AI。", "你能思考吗？", "我可以模拟思考。"]
    result = process_conversation_history(history)
    assert result == "你好\n你能思考吗？"
    assert process_conversation_history([]) == ""

# --- 测试 5: 是否正确整理最终总结 ---
def test_format_final_summary():
    assert format_final_summary("这是一段总结。") == "## 总结\n\n这是一段总结。"
    assert format_final_summary("  空格 ") == "## 总结\n\n空格"

# test_app.py
from app import (
    # 保持原有的导入...
    celsius_to_fahrenheit,
    get_max_value
)

# 请确保文件开头导入了 pytest
import pytest 

# --- 测试 6: 摄氏度转华氏度 ---
def test_celsius_to_fahrenheit():
    # 验证常规转换公式
    assert celsius_to_fahrenheit(0) == 32.0
    assert celsius_to_fahrenheit(100) == 212.0
    # 验证负数边界情况
    assert celsius_to_fahrenheit(-40) == -40.0

# --- 测试 7: 获取列表最大值 ---
def test_get_max_value():
    # 验证正常获取最大值
    assert get_max_value([1, 5, 3, 9, 2]) == 9
    
    # 验证当列表为空时，是否精准定位并抛出了对应的异常
    # 如果没有这个测试，空列表传入时程序可能会在别处崩溃，难以排查
    with pytest.raises(ValueError, match="列表不能为空"):
        get_max_value([])

# test_app.py 文件末尾追加以下代码

from app import create_ai_prompt_pipeline

# --- 测试 8 (集成测试): 完整的 AI 提示词生成流水线 ---
def test_create_ai_prompt_pipeline():
    # 1. 测试正常数据的模块间协作
    prompt = create_ai_prompt_pipeline("什么是自由？")
    # 预期结果：应该包含"存在主义"和"什么是自由？"
    assert "存在主义" in prompt
    assert "什么是自由？" in prompt
    
    # 2. 测试异常数据在流水线中的传递
    prompt_empty = create_ai_prompt_pipeline("")
    # 预期结果：应该被第一步的 validate_question 拦截，返回错误信息
    assert prompt_empty == "错误：请输入有效问题"