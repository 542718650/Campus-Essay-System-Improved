"""
Test report generator for Campus Essay System.
Generates summary reports from test results.
"""

import os
import datetime
from collections import defaultdict


def count_lines(file_path):
    """Count lines in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except Exception:
        return 0


def calculate_code_ratio():
    """Calculate test-to-application code ratio."""
    # Application code (modular structure)
    app_dirs = [
        os.path.join(os.path.dirname(__file__), '..', 'services'),
        os.path.join(os.path.dirname(__file__), '..', 'models'),
        os.path.join(os.path.dirname(__file__), '..', 'views'),
    ]
    app_files = [
        os.path.join(os.path.dirname(__file__), '..', 'config.py'),
        os.path.join(os.path.dirname(__file__), '..', 'main.py'),
    ]

    app_lines = 0
    for d in app_dirs:
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith('.py'):
                    app_lines += count_lines(os.path.join(d, f))
    for f in app_files:
        app_lines += count_lines(f)

    # Test code
    test_dir = os.path.dirname(__file__)
    test_files = [f for f in os.listdir(test_dir)
                  if f.startswith('test_') and f.endswith('.py')]

    test_lines = 0
    for f in test_files:
        test_lines += count_lines(os.path.join(test_dir, f))

    ratio = test_lines / app_lines if app_lines > 0 else 0

    return {
        'app_lines': app_lines,
        'test_lines': test_lines,
        'ratio': round(ratio, 2)
    }


def generate_test_report(test_results):
    """Generate a markdown test report from results."""
    code_ratio = calculate_code_ratio()

    report = []
    report.append("# 测试报告\n")
    report.append(f"**生成时间**: {test_results.get('timestamp', datetime.datetime.now().isoformat())}\n")

    # Summary
    report.append("## 测试摘要\n")
    report.append(f"- **总计**: {test_results['total']}")
    report.append(f"- **通过**: {test_results['passed']}")
    report.append(f"- **失败**: {test_results['failed']}")
    report.append(f"- **错误**: {test_results['errors']}")
    report.append(f"- **通过率**: {test_results['success_rate']:.1f}%\n")

    # Code ratio
    report.append("## 代码覆盖率分析\n")
    report.append(f"- **应用代码行数**: {code_ratio['app_lines']}")
    report.append(f"- **测试代码行数**: {code_ratio['test_lines']}")
    report.append(f"- **测试/应用代码比例**: {code_ratio['ratio']}:1\n")

    # Test file breakdown
    test_file_map = {
        'test_basic_functions.py': '单元测试',
        'test_llm_functions.py': 'LLM 功能测试',
        'test_system_integration.py': '系统集成测试',
        'test_acceptance.py': '验收测试',
        'test_role_auth.py': '角色认证测试',
        'test_security.py': '安全测试',
        'test_performance.py': '性能测试',
    }

    report.append("## 测试结果统计\n")
    report.append("| 测试文件 | 类型 | 用例数 | 通过 | 失败 | 错误 | 通过率 |")
    report.append("|----------|------|--------|------|------|------|--------|")

    for test_file, test_type in test_file_map.items():
        details = [d for d in test_results.get('test_details', [])
                   if d['class_name'].startswith(
                       test_file.replace('test_', 'Test').replace('.py', '')) or
                       d['class_name'] in _get_classes_for_file(test_file)]

        total = len(details)
        passed = len([d for d in details if d['status'] == 'passed'])
        failed = len([d for d in details if d['status'] == 'failed'])
        errors = len([d for d in details if d['status'] == 'error'])
        rate = (passed / total * 100) if total > 0 else 0

        report.append(
            f"| {test_file} | {test_type} | {total} | "
            f"{passed} | {failed} | {errors} | {rate:.1f}% |"
        )

    # Totals
    total = test_results['total']
    passed = test_results['passed']
    failed = test_results['failed']
    errors = test_results['errors']
    rate = test_results['success_rate']
    report.append(
        f"| **总计** | - | **{total}** | "
        f"**{passed}** | **{failed}** | **{errors}** | "
        f"**{rate:.1f}%** |"
    )

    # Failures
    failures = [d for d in test_results.get('test_details', [])
                if d['status'] in ('failed', 'error')]
    if failures:
        report.append("\n## 失败详情\n")
        for f in failures:
            report.append(f"### {f['class_name']}.{f['test_name']}\n")
            report.append(f"**状态**: {'失败' if f['status'] == 'failed' else '错误'}\n")
            if f['message']:
                report.append(f"**详情**:\n```\n{f['message'][:500]}\n```\n")

    report.append("\n---\n*报告由 test_report_generator.py 自动生成*\n")

    return "\n".join(report)


def _get_classes_for_file(test_file):
    """Map test file to expected class name prefixes."""
    mapping = {
        'test_basic_functions.py': [
            'TestChineseWordCount', 'TestParagraphCount', 'TestSentenceCount',
            'TestStructureScore', 'TestExpressionScore', 'TestCalculateTotalScore',
            'TestGenerateFeedbackSummary', 'TestPasswordHashing',
            'TestRolePermission', 'TestConfig', 'TestConstants',
        ],
        'test_llm_functions.py': [
            'TestLLMFunctions', 'TestFallbackStepRewrite',
        ],
        'test_system_integration.py': [
            'TestFullEssayReviewFlow', 'TestDatabaseAuthIntegration',
            'TestDatabaseOperationsIntegration', 'TestLLMServiceIntegration',
            'TestModuleInteractionConsistency',
        ],
        'test_acceptance.py': [
            'TestUserStories', 'TestOutputFormatAcceptance',
            'TestContentQualityAcceptance', 'TestEdgeCaseAcceptance',
        ],
        'test_role_auth.py': [
            'TestRoleAuth', 'TestRoleRegistration',
            'TestParentStudentBinding', 'TestPermissionChecks',
        ],
        'test_security.py': [
            'TestCredentialSecurity', 'TestPasswordSecurity',
            'TestSQLInjection', 'TestAuthorizationSecurity',
        ],
        'test_performance.py': [
            'TestTextMetricsPerformance', 'TestFeedbackPerformance',
            'TestDatabasePerformance', 'TestAuthPerformance',
        ],
    }
    return mapping.get(test_file, [])


def write_report_to_file(test_results, output_path=None):
    """Write test report to a markdown file."""
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(__file__), 'TEST_REPORT.md'
        )

    report = generate_test_report(test_results)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"测试报告已写入: {output_path}")
    return output_path


if __name__ == '__main__':
    from test_suite import run_all_tests
    results = run_all_tests()
    write_report_to_file(results)
