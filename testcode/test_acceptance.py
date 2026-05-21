import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from campus_essay_system import (
    fallback_feedback,
    generate_topics,
    compare_with_model_essay,
    fallback_image_prompts,
    vision_observation_prompts,
    build_prompt,
    grade_expectation,
    get_rubric_markdown
)


class TestAcceptance(unittest.TestCase):
    """验收测试（v3版本）"""
    
    def test_user_story_grade_3_narrative_essay(self):
        """测试三年级学生写记叙文的用户故事"""
        grade = "三年级"
        genre = "写事"
        theme = "一次难忘的活动"
        essay = "上周六，我们班举行了跳绳比赛。刚开始时，我很紧张，手心都出汗了。轮到我上场时，我深吸一口气，努力让自己平静下来。随着哨声响起，我飞快地跳了起来。虽然最后没有拿第一名，但我明白了只要勇敢面对，就有进步。"
        
        # 获取反馈
        feedback = fallback_feedback(grade, genre, theme, essay)
        
        # 验证反馈格式和内容
        self.assertIsInstance(feedback, dict)
        self.assertIn("teacher_feedback", feedback)
        self.assertIn("student_feedback", feedback)
        self.assertIn("strengths", feedback)
        self.assertIn("suggestions", feedback)
        self.assertIn("polished_sentence", feedback)
        self.assertIn("outline_advice", feedback)
        self.assertIn("step_rewrite", feedback)
        
        # 验证内容质量
        self.assertIsInstance(feedback["strengths"], list)
        self.assertIsInstance(feedback["suggestions"], list)
        self.assertTrue(len(feedback["strengths"]) >= 3)
        self.assertTrue(len(feedback["suggestions"]) >= 3)
    
    def test_user_story_grade_5_descriptive_essay(self):
        """测试五年级学生写写景作文的用户故事"""
        grade = "五年级"
        genre = "写景"
        theme = "秋天的校园"
        essay = "秋天的校园真美。操场边的银杏树像撑开的一把把金色小伞，风一吹，叶子轻轻落下来，像一只只蝴蝶在飞。花坛里的菊花开得正热闹，有黄的、白的、紫的，把校园装扮得五彩缤纷。"
        
        # 获取反馈
        feedback = fallback_feedback(grade, genre, theme, essay)
        
        # 验证反馈格式和内容
        self.assertIsInstance(feedback, dict)
        self.assertIn("teacher_feedback", feedback)
        self.assertIn("student_feedback", feedback)
        self.assertIn("strengths", feedback)
        self.assertIn("suggestions", feedback)
    
    def test_user_story_short_essay_handling(self):
        """测试短作文处理的用户故事"""
        grade = "三年级"
        genre = "写人"
        theme = "我的好朋友"
        short_essay = "我的好朋友是小明。他很聪明。"
        
        # 获取反馈
        feedback = fallback_feedback(grade, genre, theme, short_essay)
        
        # 验证短作文的反馈内容
        self.assertIn("字数还可以再充实一些", feedback["suggestions"][0])
    
    def test_user_story_empty_input_handling(self):
        """测试空输入处理的用户故事"""
        grade = "四年级"
        genre = "写事"
        theme = "难忘的一天"
        empty_essay = ""
        
        # 获取反馈（不应崩溃）
        feedback = fallback_feedback(grade, genre, theme, empty_essay)
        
        # 验证反馈格式正确
        self.assertIsInstance(feedback, dict)
        self.assertIn("teacher_feedback", feedback)
    
    def test_user_story_complex_essay_with_dialogue(self):
        """测试包含对话的复杂作文的用户故事"""
        grade = "六年级"
        genre = "写事"
        theme = "一次有趣的对话"
        essay = "\"妈妈，今天我们去公园玩好不好？\"我兴奋地问。\"好啊，\"妈妈笑着说，\"但是你要先完成作业。\"我点点头，赶紧跑回房间写作业。写完作业后，我们开开心心地去了公园。"
        
        # 获取反馈
        feedback = fallback_feedback(grade, genre, theme, essay)
        
        # 验证反馈格式正确
        self.assertIsInstance(feedback, dict)
        self.assertIn("teacher_feedback", feedback)
    
    def test_acceptance_criteria_output_format(self):
        """测试输出格式验证的验收标准"""
        grade = "四年级"
        genre = "写人"
        theme = "我的老师"
        essay = "我的老师姓王，她很温柔。每次我有问题，她都会耐心地教我。"
        
        # 获取反馈
        feedback = fallback_feedback(grade, genre, theme, essay)
        
        # 验证反馈为字典格式
        self.assertIsInstance(feedback, dict)
        
        # 验证包含所有必要字段
        required_fields = ["teacher_feedback", "student_feedback", "strengths", "suggestions", "polished_sentence", "outline_advice", "step_rewrite"]
        for field in required_fields:
            self.assertIn(field, feedback)
        
        # 验证各字段类型正确
        self.assertIsInstance(feedback["teacher_feedback"], str)
        self.assertIsInstance(feedback["student_feedback"], str)
        self.assertIsInstance(feedback["strengths"], list)
        self.assertIsInstance(feedback["suggestions"], list)
        self.assertIsInstance(feedback["polished_sentence"], str)
        self.assertIsInstance(feedback["outline_advice"], str)
        self.assertIsInstance(feedback["step_rewrite"], dict)
    
    def test_acceptance_criteria_content_quality(self):
        """测试内容质量验证的验收标准"""
        grade = "五年级"
        genre = "写景"
        theme = "美丽的公园"
        essay = "公园的春天真美。花儿开了，草儿绿了，小鸟在唱歌。我喜欢春天的公园。"
        
        # 获取反馈
        feedback = fallback_feedback(grade, genre, theme, essay)
        
        # 验证内容质量要求
        self.assertGreaterEqual(len(feedback.get("strengths", [])), 3)
        self.assertGreaterEqual(len(feedback.get("suggestions", [])), 3)
        self.assertGreaterEqual(len(feedback.get("polished_sentence", [])), 2)
        self.assertGreaterEqual(len(feedback.get("outline_advice", [])), 3)
    
    def test_acceptance_criteria_sample_comparison(self):
        """测试范文对比功能的验收标准"""
        grade = "四年级"
        genre = "写人"
        essay = "我的妈妈很爱我。每天早上，她都会给我做早餐。"
        
        # 进行范文对比
        compare_result = compare_with_model_essay(essay, genre, "我的妈妈")
        
        # 验证对比结果格式
        self.assertIsInstance(compare_result, str)
        self.assertTrue(len(compare_result) > 0)
        self.assertIn("范文对比提示", compare_result)
    
    def test_acceptance_criteria_topic_generation(self):
        """测试题目生成功能的验收标准"""
        grade = "五年级"
        genre = "想象作文"
        
        # 生成主题选项
        topics = generate_topics(grade, genre)
        
        # 验证主题选项
        self.assertIsInstance(topics, list)
        self.assertGreaterEqual(len(topics), 3)
        
        # 生成关键词主题
        topics_with_keyword = generate_topics(grade, genre, "未来")
        
        # 验证主题选项
        self.assertIsInstance(topics_with_keyword, list)
        self.assertGreaterEqual(len(topics_with_keyword), 3)
        # 验证包含关键词
        keyword_found = any("未来" in topic for topic in topics_with_keyword)
        self.assertTrue(keyword_found)
    
    def test_acceptance_criteria_image_prompts(self):
        """测试图片提示功能的验收标准"""
        grade = "四年级"
        
        # 获取回退图片提示
        prompts = fallback_image_prompts(grade)
        
        # 验证图片提示格式
        self.assertIsInstance(prompts, dict)
        self.assertIn("scene", prompts)
        self.assertIn("observe", prompts)
        self.assertIn("questions", prompts)
        self.assertIn("suggested_title", prompts)
        
        # 验证内容质量
        self.assertIsInstance(prompts["scene"], str)
        self.assertIsInstance(prompts["observe"], list)
        self.assertIsInstance(prompts["questions"], list)
        self.assertIsInstance(prompts["suggested_title"], str)
        self.assertEqual(len(prompts["observe"]), 4)
        self.assertEqual(len(prompts["questions"]), 4)
    
    def test_acceptance_criteria_build_prompt(self):
        """测试构建提示功能的验收标准"""
        grade = "三年级"
        genre = "写人"
        theme = "我的妈妈"
        essay = "我的妈妈很爱我。"
        
        # 构建提示
        prompt = build_prompt(grade, genre, theme, essay)
        
        # 验证提示格式
        self.assertIsInstance(prompt, str)
        self.assertTrue(len(prompt) > 0)
        self.assertIn(grade, prompt)
        self.assertIn(genre, prompt)
        self.assertIn(theme, prompt)
        self.assertIn(essay, prompt)
    
    def test_acceptance_criteria_grade_expectation(self):
        """测试年级期望功能的验收标准"""
        grade = "三年级"
        
        # 获取年级期望
        expectation = grade_expectation(grade)
        
        # 验证期望格式
        self.assertIsInstance(expectation, str)
        self.assertTrue(len(expectation) > 0)
    
    def test_acceptance_criteria_get_rubric_markdown(self):
        """测试获取评分标准markdown功能的验收标准"""
        grade = "三年级"
        
        # 获取评分标准markdown
        markdown = get_rubric_markdown(grade)
        
        # 验证markdown格式
        self.assertIsInstance(markdown, str)
        self.assertTrue(len(markdown) > 0)


if __name__ == '__main__':
    unittest.main()
