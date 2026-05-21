import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from campus_essay_system import (
    llm_json_feedback,
    fallback_feedback,
    generate_topics,
    compare_with_model_essay,
    text_to_data_url,
    fallback_image_prompts,
    vision_observation_prompts,
    build_prompt,
    grade_expectation,
    get_rubric_markdown
)


class TestLLMFunctions(unittest.TestCase):
    """测试LLM相关功能（v3版本）"""
    
    def test_fallback_feedback(self):
        """测试回退反馈功能"""
        feedback = fallback_feedback("三年级", "写人", "我的妈妈", "这是一篇测试作文。")
        
        # 验证回退反馈的结构
        self.assertIn("teacher_feedback", feedback)
        self.assertIn("student_feedback", feedback)
        self.assertIn("strengths", feedback)
        self.assertIn("suggestions", feedback)
        self.assertIn("polished_sentence", feedback)
        self.assertIn("outline_advice", feedback)
        self.assertIn("step_rewrite", feedback)
        
        # 验证内容类型
        self.assertIsInstance(feedback["strengths"], list)
        self.assertIsInstance(feedback["suggestions"], list)
        self.assertIsInstance(feedback["step_rewrite"], dict)
    
    def test_fallback_feedback_short_essay(self):
        """测试短作文的回退反馈"""
        short_essay = "很短。"
        feedback = fallback_feedback("三年级", "写事", "一次活动", short_essay)
        
        self.assertIn("字数还可以再充实一些", feedback["suggestions"][0])
    
    def test_fallback_feedback_normal_essay(self):
        """测试正常长度作文的回退反馈"""
        normal_essay = "这是一篇正常长度的作文。今天天气很好，我和同学们一起去公园玩。"
        feedback = fallback_feedback("三年级", "写景", "秋天的公园", normal_essay)
        
        self.assertIsInstance(feedback["strengths"], list)
        self.assertTrue(len(feedback["strengths"]) >= 3)
        self.assertTrue(len(feedback["suggestions"]) >= 3)
    
    def test_generate_topics(self):
        """测试生成主题功能"""
        topics = generate_topics("三年级", "写人")
        self.assertIsInstance(topics, list)
        self.assertTrue(len(topics) > 0)
        
        topics_with_keyword = generate_topics("三年级", "写人", "足球")
        self.assertIsInstance(topics_with_keyword, list)
        self.assertTrue(len(topics_with_keyword) > 0)
        
        # 验证关键词出现在主题中
        self.assertIn("足球", topics_with_keyword[0])
    
    def test_compare_with_model_essay(self):
        """测试与范文对比功能"""
        result = compare_with_model_essay("学生作文", "写事", "一次活动")
        
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        self.assertIn("范文对比提示", result)
    
    def test_fallback_image_prompts(self):
        """测试回退图片提示功能"""
        prompts = fallback_image_prompts("三年级")
        
        self.assertIn("scene", prompts)
        self.assertIn("observe", prompts)
        self.assertIn("questions", prompts)
        self.assertIn("suggested_title", prompts)
        self.assertEqual(len(prompts["observe"]), 4)
        self.assertEqual(len(prompts["questions"]), 4)
    
    def test_build_prompt(self):
        """测试构建提示功能"""
        prompt = build_prompt("三年级", "写人", "我的妈妈", "这是一篇测试作文。")
        
        # 验证提示包含所有必要信息
        self.assertIn("三年级", prompt)
        self.assertIn("写人", prompt)
        self.assertIn("我的妈妈", prompt)
        self.assertIn("这是一篇测试作文。", prompt)
    
    def test_grade_expectation(self):
        """测试年级期望功能"""
        expectation = grade_expectation("三年级")
        self.assertIsInstance(expectation, str)
        self.assertTrue(len(expectation) > 0)
    
    def test_get_rubric_markdown(self):
        """测试获取评分标准markdown功能"""
        markdown = get_rubric_markdown("三年级")
        self.assertIsInstance(markdown, str)
        self.assertTrue(len(markdown) > 0)


if __name__ == '__main__':
    unittest.main()
