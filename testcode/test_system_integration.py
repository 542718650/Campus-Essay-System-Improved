import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from campus_essay_system import (
    chinese_word_count,
    paragraph_count,
    sentence_count,
    has_beginning_middle_end,
    structure_level,
    expression_level,
    infer_structure_score,
    infer_expression_score,
    llm_json_feedback,
    fallback_feedback,
    generate_topics,
    compare_with_model_essay,
    DEFAULT_TOPICS,
    ESSAY_TEMPLATES,
    GRADE_RUBRICS
)


class TestSystemIntegration(unittest.TestCase):
    """测试系统集成功能（v3版本）"""
    
    def test_full_essay_review_flow(self):
        """测试完整的作文点评流程"""
        # 构建作文数据
        grade = "三年级"
        genre = "写人"
        theme = "我的妈妈"
        essay = "我的妈妈很爱我。每天早上，她都会给我做早餐。有一次我生病了，妈妈一直照顾我。我觉得妈妈是世界上最好的人。"
        
        # 调用反馈生成功能
        feedback = fallback_feedback(grade, genre, theme, essay)
        
        # 验证反馈结构完整性
        self.assertIn("teacher_feedback", feedback)
        self.assertIn("student_feedback", feedback)
        self.assertIn("strengths", feedback)
        self.assertIn("suggestions", feedback)
        self.assertIn("polished_sentence", feedback)
        self.assertIn("outline_advice", feedback)
        self.assertIn("step_rewrite", feedback)
    
    def test_character_count_and_feedback_integration(self):
        """测试字符计数与反馈生成的集成"""
        essay = "这是一篇测试作文。今天天气很好，我和同学们一起去公园玩。"
        char_count = chinese_word_count(essay)
        
        feedback = fallback_feedback("三年级", "写事", "一次活动", essay)
        
        # 验证字符计数结果合理
        self.assertGreater(char_count, 0)
        
        # 验证反馈内容与作文长度相关
        if char_count < 120:
            self.assertIn("字数还可以再充实一些", feedback["suggestions"][0])
    
    def test_error_handling_in_integration(self):
        """测试集成过程中的错误处理"""
        # 测试空作文处理
        empty_essay = ""
        feedback = fallback_feedback("三年级", "写人", "测试主题", empty_essay)
        
        # 验证系统不会崩溃，能返回合理的反馈
        self.assertIsInstance(feedback, dict)
        self.assertIn("teacher_feedback", feedback)
    
    def test_full_workflow_with_short_essay(self):
        """测试短作文场景的完整工作流"""
        short_essay = "很短。"
        feedback = fallback_feedback("三年级", "写事", "测试主题", short_essay)
        
        # 验证短作文反馈
        self.assertIn("字数还可以再充实一些", feedback["suggestions"][0])
    
    def test_full_workflow_with_normal_essay(self):
        """测试正常长度作文场景的完整工作流"""
        normal_essay = "这是一篇正常长度的作文。今天天气很好，我和同学们一起去公园玩。我们玩了很多游戏，非常开心。公园里的花儿开得很美，有红色的玫瑰、黄色的菊花，还有紫色的薰衣草。我们在草地上奔跑、追逐，玩得不亦乐乎。不知不觉中，太阳慢慢西沉，我们恋恋不舍地离开了公园。今天真是难忘的一天，我和朋友们度过了美好的时光。"
        
        # 测试反馈生成
        feedback = fallback_feedback("三年级", "写景", "秋天的公园", normal_essay)
        self.assertIsInstance(feedback, dict)
        
        # 测试范文对比
        compare_result = compare_with_model_essay(normal_essay, "写景", "秋天的公园")
        self.assertIsInstance(compare_result, str)
    
    def test_topic_generation_integration(self):
        """测试主题生成功能的集成"""
        # 测试主题生成
        topics = generate_topics("三年级", "写人")
        self.assertIsInstance(topics, list)
        self.assertTrue(len(topics) > 0)
        
        # 测试关键词主题生成
        topics_with_keyword = generate_topics("三年级", "写人", "足球")
        self.assertIsInstance(topics_with_keyword, list)
        self.assertTrue(len(topics_with_keyword) > 0)
        
        # 验证关键词出现在主题中
        self.assertIn("足球", topics_with_keyword[0])
    
    def test_structure_and_expression_evaluation(self):
        """测试结构和表达水平评估功能"""
        essay = "这是第一段。\n这是第二段。\n这是第三段。好像天气很好，于是我们就去公园玩。"
        
        structure = structure_level(essay)
        expression = expression_level(essay)
        
        # 验证评估结果
        self.assertIn(structure, ["较完整", "基本完整", "待加强"])
        self.assertIn(expression, ["较丰富", "一般", "待丰富"])
    
    def test_infer_scores_integration(self):
        """测试得分推断功能的集成"""
        essay = "这是一篇测试作文。今天天气很好，我和同学们一起去公园玩。"
        
        # 测试结构得分推断
        structure_score = infer_structure_score(essay)
        self.assertGreaterEqual(structure_score, 60)
        self.assertLessEqual(structure_score, 100)
        
        # 测试表达得分推断
        expression_score = infer_expression_score(essay)
        self.assertGreaterEqual(expression_score, 60)
        self.assertLessEqual(expression_score, 100)
    
    def test_module_interaction_consistency(self):
        """测试不同模块间的交互一致性"""
        essay = "这是一篇测试作文。今天天气很好，我和同学们一起去公园玩。"
        
        # 测试字符计数和段落计数的一致性
        char_count = chinese_word_count(essay)
        para_count = paragraph_count(essay)
        sent_count = sentence_count(essay)
        
        # 测试结构完整性检查
        has_structure = has_beginning_middle_end(essay)
        
        # 测试结构水平评估
        structure = structure_level(essay)
        
        # 测试表达水平评估
        expression = expression_level(essay)
        
        # 验证各模块返回合理结果
        self.assertGreater(char_count, 0)
        self.assertGreaterEqual(para_count, 1)
        self.assertGreaterEqual(sent_count, 1)
        self.assertIsInstance(has_structure, bool)
        self.assertIn(structure, ["较完整", "基本完整", "待加强"])
        self.assertIn(expression, ["较丰富", "一般", "待丰富"])


if __name__ == '__main__':
    unittest.main()
