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
    DEFAULT_TOPICS,
    ESSAY_TEMPLATES,
    GRADE_RUBRICS
)


class TestBasicFunctions(unittest.TestCase):
    """测试基础功能函数"""
    
    def test_chinese_word_count(self):
        """测试中文字符计数功能"""
        self.assertEqual(chinese_word_count(""), 0)
        self.assertEqual(chinese_word_count("你好"), 2)
        self.assertEqual(chinese_word_count("Hello 世界"), 2)
        self.assertEqual(chinese_word_count("今天天气真好！"), 6)
        self.assertEqual(chinese_word_count("123中文abc"), 2)
    
    def test_chinese_word_count_with_special_chars(self):
        """测试包含特殊字符的中文字符计数"""
        text = "这是一篇作文！包含标点符号，数字123，字母abc。"
        self.assertEqual(chinese_word_count(text), 16)
    
    def test_chinese_word_count_edge_cases(self):
        """测试中文字符计数的边界情况"""
        # 全角字符测试
        self.assertEqual(chinese_word_count("ａｂｃ１２３"), 0)
        # 中文标点测试
        self.assertEqual(chinese_word_count("，。！？：；""''"), 0)
        # 混合文本测试
        self.assertEqual(chinese_word_count("Hello 世界123你好abc"), 4)
    
    def test_infer_structure_score(self):
        """测试结构得分推断功能"""
        # 短文本测试
        score1 = infer_structure_score("很短的文章。")
        self.assertGreaterEqual(score1, 60)
        self.assertLessEqual(score1, 70)
        
        # 长文本测试
        long_text = "这是一篇较长的文章。" * 20
        score2 = infer_structure_score(long_text)
        self.assertGreaterEqual(score2, 70)
    
    def test_infer_expression_score(self):
        """测试表达得分推断功能"""
        # 简单表达测试
        score1 = infer_expression_score("他很高兴。")
        self.assertGreaterEqual(score1, 60)
        self.assertLessEqual(score1, 70)
        
        # 丰富表达测试
        rich_text = "他兴高采烈地跑过来，脸上洋溢着灿烂的笑容，眼睛里闪烁着兴奋的光芒。"
        score2 = infer_expression_score(rich_text)
        self.assertGreaterEqual(score2, 60)
    
    def test_paragraph_count(self):
        """测试段落计数功能"""
        self.assertEqual(paragraph_count(""), 0)
        self.assertEqual(paragraph_count("这是一段文字。"), 1)
        self.assertEqual(paragraph_count("第一段\n第二段"), 2)
        self.assertEqual(paragraph_count("第一段\n\n第二段"), 2)
        self.assertEqual(paragraph_count("第一段\n\n\n第二段\n第三段"), 3)
    
    def test_sentence_count(self):
        """测试句子计数功能"""
        self.assertEqual(sentence_count(""), 0)
        self.assertEqual(sentence_count("这是一个句子。"), 1)
        self.assertEqual(sentence_count("这是第一个句子。这是第二个句子！"), 2)
        self.assertEqual(sentence_count("Hello. World!"), 2)
        self.assertEqual(sentence_count("这是句子？是的！"), 2)
    
    def test_has_beginning_middle_end(self):
        """测试文章结构完整性检查"""
        # 段落数足够
        self.assertTrue(has_beginning_middle_end("第一段\n第二段\n第三段"))
        # 句子数足够
        self.assertTrue(has_beginning_middle_end("第一句。第二句。第三句。第四句。第五句。"))
        # 段落数不足但句子数足够
        self.assertTrue(has_beginning_middle_end("第一句。第二句。第三句。第四句。第五句。第六句。"))
        # 都不足
        self.assertFalse(has_beginning_middle_end("第一句。第二句。"))
    
    def test_structure_level(self):
        """测试结构水平评估"""
        # 较完整（3个段落，每个段落至少2个句子）
        self.assertEqual(structure_level("第一段第一句。第一段第二句。\n第二段第一句。第二段第二句。\n第三段第一句。第三段第二句。"), "较完整")
        # 基本完整（4个句子）
        self.assertEqual(structure_level("第一段。第二段。第三段。第四句。"), "基本完整")
        # 待加强（只有2个句子）
        self.assertEqual(structure_level("第一句。第二句。"), "待加强")
    
    def test_expression_level(self):
        """测试表达水平评估"""
        # 待丰富
        self.assertEqual(expression_level("好像他在笑，心里很高兴，于是就跑过去。"), "待丰富")
        # 待丰富
        self.assertEqual(expression_level("他笑了，心里很高兴。"), "待丰富")
        # 待丰富
        self.assertEqual(expression_level("他很高兴。"), "待丰富")
    
    def test_constants_validation(self):
        """测试常量定义的有效性"""
        self.assertIsInstance(DEFAULT_TOPICS, dict)
        self.assertIsInstance(ESSAY_TEMPLATES, dict)
        self.assertIsInstance(GRADE_RUBRICS, dict)
        
        self.assertTrue(len(DEFAULT_TOPICS) > 0)
        self.assertTrue(len(ESSAY_TEMPLATES) > 0)
        self.assertTrue(len(GRADE_RUBRICS) > 0)
    
    def test_constants_content_validation(self):
        """测试常量内容的有效性"""
        # 验证年级评分标准
        self.assertIn("三年级", GRADE_RUBRICS)
        self.assertIn("六年级", GRADE_RUBRICS)
        
        # 验证作文模板
        self.assertIn("写人", ESSAY_TEMPLATES)
        self.assertIn("写事", ESSAY_TEMPLATES)
        self.assertIn("看图作文", ESSAY_TEMPLATES)
        
        # 验证默认主题
        self.assertIn("写人", DEFAULT_TOPICS)
        self.assertIn("写事", DEFAULT_TOPICS)
        self.assertIn("看图作文", DEFAULT_TOPICS)


if __name__ == '__main__':
    unittest.main()