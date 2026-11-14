import pytest
from app import create_ai_prompt_pipeline, celsius_to_fahrenheit, get_max_value

class TestAppIntegration:
    
    def test_pipeline_normal(self):
        """TC-INT-01: 正常流程集成测试"""
        result = create_ai_prompt_pipeline("什么是自由？")
        expected = "你是一位存在主义哲学家，请回答以下问题：什么是自由？"
        assert result == expected

    def test_pipeline_no_keyword(self):
        """TC-INT-02: 无关键词时的兜底测试"""
        result = create_ai_prompt_pipeline("今天天气怎么样？")
        expected = "你是一位其他哲学视角哲学家，请回答以下问题：今天天气怎么样？"
        assert result == expected

    def test_pipeline_invalid_input(self):
        """TC-INT-03: 异常输入拦截测试"""
        result = create_ai_prompt_pipeline("   ")
        assert result == "错误：请输入有效问题"

    def test_celsius_to_fahrenheit(self):
        """TC-INT-04: 摄氏度转华氏度功能"""
        assert celsius_to_fahrenheit(0) == 32.0
        assert celsius_to_fahrenheit(100) == 212.0
        assert celsius_to_fahrenheit(-40) == -40.0

    def test_get_max_value_exception(self):
        """TC-INT-05: 获取最大值时的异常处理"""
        assert get_max_value([1, 5, 3]) == 5
        with pytest.raises(ValueError, match="列表不能为空"):
            get_max_value([])