"""
Test suite runner for Campus Essay System.
Runs all test modules and collects results.
"""

import unittest
import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_all_tests():
    """Run all tests and collect detailed results."""
    print("开始运行 Campus Essay System 测试套件...")
    print("=" * 60)

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    # Import all test classes
    from test_basic_functions import (
        TestChineseWordCount, TestParagraphCount, TestSentenceCount,
        TestStructureScore, TestExpressionScore, TestCalculateTotalScore,
        TestGenerateFeedbackSummary, TestPasswordHashing,
        TestRolePermission, TestConfig, TestConstants
    )
    from test_llm_functions import (
        TestLLMFunctions, TestFallbackStepRewrite
    )
    from test_system_integration import (
        TestFullEssayReviewFlow, TestDatabaseAuthIntegration,
        TestDatabaseOperationsIntegration, TestLLMServiceIntegration,
        TestModuleInteractionConsistency
    )
    from test_acceptance import (
        TestUserStories, TestOutputFormatAcceptance,
        TestContentQualityAcceptance, TestEdgeCaseAcceptance
    )
    from test_role_auth import (
        TestRoleAuth, TestRoleRegistration,
        TestParentStudentBinding, TestPermissionChecks
    )
    from test_security import (
        TestCredentialSecurity, TestPasswordSecurity,
        TestSQLInjection, TestAuthorizationSecurity
    )
    from test_performance import (
        TestTextMetricsPerformance, TestFeedbackPerformance,
        TestDatabasePerformance, TestAuthPerformance
    )

    # Add all test classes
    for test_class in [
        TestChineseWordCount, TestParagraphCount, TestSentenceCount,
        TestStructureScore, TestExpressionScore, TestCalculateTotalScore,
        TestGenerateFeedbackSummary, TestPasswordHashing,
        TestRolePermission, TestConfig, TestConstants,
        TestLLMFunctions, TestFallbackStepRewrite,
        TestFullEssayReviewFlow, TestDatabaseAuthIntegration,
        TestDatabaseOperationsIntegration, TestLLMServiceIntegration,
        TestModuleInteractionConsistency,
        TestUserStories, TestOutputFormatAcceptance,
        TestContentQualityAcceptance, TestEdgeCaseAcceptance,
        TestRoleAuth, TestRoleRegistration,
        TestParentStudentBinding, TestPermissionChecks,
        TestCredentialSecurity, TestPasswordSecurity,
        TestSQLInjection, TestAuthorizationSecurity,
        TestTextMetricsPerformance, TestFeedbackPerformance,
        TestDatabasePerformance, TestAuthPerformance,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    # Run with custom result collector
    result_collector = _DetailedResultCollector()
    runner = unittest.TextTestRunner(
        resultclass=_DetailedResultCollector, verbosity=2
    )
    result = runner.run(suite)

    # Collect results
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)

    return {
        'total': total,
        'passed': passed,
        'failed': len(result.failures),
        'errors': len(result.errors),
        'success_rate': passed / total * 100 if total > 0 else 0,
        'test_details': result_collector.test_results,
        'timestamp': datetime.datetime.now().isoformat()
    }


def run_test_category(category):
    """Run tests by category."""
    print(f"开始运行 {category} 测试...")
    print("=" * 60)

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    category_map = {
        'unit': [
            'test_basic_functions.TestChineseWordCount',
            'test_basic_functions.TestParagraphCount',
            'test_basic_functions.TestSentenceCount',
            'test_basic_functions.TestStructureScore',
            'test_basic_functions.TestExpressionScore',
            'test_basic_functions.TestCalculateTotalScore',
            'test_basic_functions.TestGenerateFeedbackSummary',
            'test_basic_functions.TestPasswordHashing',
            'test_basic_functions.TestRolePermission',
            'test_basic_functions.TestConfig',
            'test_basic_functions.TestConstants',
        ],
        'llm': [
            'test_llm_functions.TestLLMFunctions',
            'test_llm_functions.TestFallbackStepRewrite',
        ],
        'integration': [
            'test_system_integration.TestFullEssayReviewFlow',
            'test_system_integration.TestDatabaseAuthIntegration',
            'test_system_integration.TestDatabaseOperationsIntegration',
            'test_system_integration.TestLLMServiceIntegration',
            'test_system_integration.TestModuleInteractionConsistency',
        ],
        'acceptance': [
            'test_acceptance.TestUserStories',
            'test_acceptance.TestOutputFormatAcceptance',
            'test_acceptance.TestContentQualityAcceptance',
            'test_acceptance.TestEdgeCaseAcceptance',
        ],
        'role': [
            'test_role_auth.TestRoleAuth',
            'test_role_auth.TestRoleRegistration',
            'test_role_auth.TestParentStudentBinding',
            'test_role_auth.TestPermissionChecks',
        ],
        'security': [
            'test_security.TestCredentialSecurity',
            'test_security.TestPasswordSecurity',
            'test_security.TestSQLInjection',
            'test_security.TestAuthorizationSecurity',
        ],
        'performance': [
            'test_performance.TestTextMetricsPerformance',
            'test_performance.TestFeedbackPerformance',
            'test_performance.TestDatabasePerformance',
            'test_performance.TestAuthPerformance',
        ],
    }

    if category not in category_map:
        print(f"未知的测试类别: {category}")
        print(f"可用类别: {', '.join(category_map.keys())}")
        return False

    for test_name in category_map[category]:
        suite.addTests(loader.loadTestsFromName(test_name))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


class _DetailedResultCollector(unittest.TestResult):
    """Collects detailed test results for reporting."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_results = []
        self.start_time = None
        self.end_time = None

    def startTest(self, test):
        self.start_time = datetime.datetime.now()
        super().startTest(test)

    def stopTest(self, test):
        self.end_time = datetime.datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()

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

        self.test_results.append({
            'class_name': test.__class__.__name__,
            'test_name': test._testMethodName,
            'status': status,
            'message': message,
            'duration': duration
        })

        super().stopTest(test)


def main():
    """Main entry point."""
    print("=" * 60)
    print("校园作文辅导系统 自动测试脚本")
    print("=" * 60)
    print()

    test_results = run_all_tests()

    print()
    if test_results['failed'] == 0 and test_results['errors'] == 0:
        print("=" * 60)
        print("🎉 测试全部通过！")
        print(f"  总计: {test_results['total']} | "
              f"通过: {test_results['passed']} | "
              f"通过率: {test_results['success_rate']:.1f}%")
        print("=" * 60)
    else:
        print("=" * 60)
        print("❌ 测试存在失败")
        print(f"  总计: {test_results['total']} | "
              f"通过: {test_results['passed']} | "
              f"失败: {test_results['failed']} | "
              f"错误: {test_results['errors']}")
        print("=" * 60)

    sys.exit(0 if test_results['failed'] == 0 and test_results['errors'] == 0 else 1)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        category = sys.argv[1]
        success = run_test_category(category)
        sys.exit(0 if success else 1)
    else:
        main()
