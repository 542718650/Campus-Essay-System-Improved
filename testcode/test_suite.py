import unittest
import sys
import os
import datetime
import subprocess


def check_python_installation():
    """检查Python是否安装"""
    try:
        subprocess.run([sys.executable, "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_dependencies():
    """检查并安装项目依赖"""
    print("正在检查项目依赖...")
    
    dependencies = ['streamlit']
    
    for dep in dependencies:
        try:
            subprocess.run(
                [sys.executable, "-c", f"import {dep}; print('✅ {dep}已安装')"],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError:
            print(f"❌ 缺少依赖：{dep}")
            print(f"正在安装依赖：{dep}...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"✅ {dep}安装成功")
            except subprocess.CalledProcessError as e:
                print(f"❌ {dep}安装失败: {e.stderr}")
                return False
    return True


def pause_before_exit():
    """仅在交互式终端中等待用户确认退出。"""
    if sys.stdin.isatty():
        input("按回车键退出...")


class TestResultCollector(unittest.TestResult):
    """自定义测试结果收集器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    def startTest(self, test):
        """测试开始时记录时间"""
        self.start_time = datetime.datetime.now()
        super().startTest(test)
    
    def stopTest(self, test):
        """测试结束时记录结果"""
        self.end_time = datetime.datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        # 确定测试状态
        status = 'passed'
        message = ''
        
        if test in self.failures:
            status = 'failed'
            for t, err in self.failures:
                if t == test:
                    message = err
                    break
        elif test in self.errors:
            status = 'error'
            for t, err in self.errors:
                if t == test:
                    message = err
                    break
        
        # 记录测试详情
        class_name = test.__class__.__name__
        test_name = test._testMethodName
        
        self.test_results.append({
            'class_name': class_name,
            'test_name': test_name,
            'status': status,
            'message': message,
            'duration': duration
        })
        
        super().stopTest(test)


def run_all_tests():
    """运行所有测试并收集详细结果"""
    print("开始运行 v3 版本测试套件...")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试用例 - 使用TestLoader替代makeSuite
    loader = unittest.TestLoader()
    
    # 动态导入测试模块
    from test_basic_functions import TestBasicFunctions
    from test_llm_functions import TestLLMFunctions
    from test_system_integration import TestSystemIntegration
    from test_acceptance import TestAcceptance
    from test_role_auth import TestRoleAuth
    from test_security import TestSecurity
    from test_performance import TestPerformance
    
    suite.addTests(loader.loadTestsFromTestCase(TestBasicFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestAcceptance))
    suite.addTests(loader.loadTestsFromTestCase(TestRoleAuth))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurity))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    
    # 使用自定义结果收集器运行测试
    result_collector = TestResultCollector()
    runner = unittest.TextTestRunner(resultclass=TestResultCollector, verbosity=2)
    result = runner.run(suite)
    
    # 统计测试结果
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    failed = len(result.failures)
    errors = len(result.errors)
    
    # 返回测试结果数据
    return {
        'total': total,
        'passed': passed,
        'failed': failed,
        'errors': errors,
        'success_rate': passed/total*100 if total > 0 else 0,
        'test_details': result.test_results,
        'timestamp': datetime.datetime.now().isoformat()
    }


def run_test_category(category):
    """按类别运行测试"""
    print(f"开始运行 {category} 测试...")
    print("=" * 60)
    
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # 动态导入测试模块
    from test_basic_functions import TestBasicFunctions
    from test_llm_functions import TestLLMFunctions
    from test_system_integration import TestSystemIntegration
    from test_acceptance import TestAcceptance
    from test_role_auth import TestRoleAuth
    from test_security import TestSecurity
    from test_performance import TestPerformance
    
    if category == 'basic':
        suite.addTests(loader.loadTestsFromTestCase(TestBasicFunctions))
    elif category == 'llm':
        suite.addTests(loader.loadTestsFromTestCase(TestLLMFunctions))
    elif category == 'system':
        suite.addTests(loader.loadTestsFromTestCase(TestSystemIntegration))
    elif category == 'acceptance':
        suite.addTests(loader.loadTestsFromTestCase(TestAcceptance))
    elif category == 'role':
        suite.addTests(loader.loadTestsFromTestCase(TestRoleAuth))
    elif category == 'security':
        suite.addTests(loader.loadTestsFromTestCase(TestSecurity))
    elif category == 'performance':
        suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    else:
        print(f"未知的测试类别: {category}")
        return False
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def main():
    """主函数：整合批命令功能，实现跨平台一键测试"""
    print("=" * 60)
    print("妙妙作文屋 v3 版本自动测试脚本")
    print("=" * 60)
    print()
    
    # 检查Python安装
    if not check_python_installation():
        print("❌ 错误：未安装Python或Python不在系统路径中")
        pause_before_exit()
        sys.exit(1)
    
    print("✅ Python已安装")
    print()
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 依赖检查失败")
        pause_before_exit()
        sys.exit(1)
    
    print()
    print("正在运行测试套件...")
    print("=" * 60)
    
    # 运行测试
    test_results = run_all_tests()
    
    # 更新README.md文件
    from test_report_generator import update_readme_with_results
    update_readme_with_results(test_results)
    
    # 显示结果
    print()
    if test_results['failed'] == 0 and test_results['errors'] == 0:
        print("=" * 60)
        print("🎉 测试全部通过！")
        print("=" * 60)
    else:
        print("=" * 60)
        print("❌ 测试失败，请检查README.md中的失败详情")
        print("=" * 60)
    
    print()
    print("=" * 60)
    print("📊 测试结果已更新到README.md文件")
    print("=" * 60)
    
    # 直接退出，不等待用户输入（适用于CI/CD环境）
    sys.exit(0 if test_results['failed'] == 0 and test_results['errors'] == 0 else 1)


if __name__ == '__main__':
    # 检查命令行参数
    if len(sys.argv) > 1:
        category = sys.argv[1]
        success = run_test_category(category)
        sys.exit(0 if success else 1)
    else:
        main()
