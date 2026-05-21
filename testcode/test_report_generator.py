import os
import datetime
from collections import defaultdict

def count_lines(file_path):
    """统计文件行数"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except Exception:
        return 0

def calculate_code_ratio():
    """计算测试代码与应用功能代码的比例"""
    # 应用功能代码
    app_file = os.path.join(os.path.dirname(__file__), '..', 'campus_essay_system.py')
    app_lines = count_lines(app_file)
    
    # 测试代码
    test_dir = os.path.dirname(__file__)
    test_files = [f for f in os.listdir(test_dir) if f.startswith('test_') and f.endswith('.py')]
    
    test_lines = 0
    for test_file in test_files:
        test_lines += count_lines(os.path.join(test_dir, test_file))
    
    if app_lines == 0:
        ratio = 0
    else:
        ratio = test_lines / app_lines
    
    return {
        'app_lines': app_lines,
        'test_lines': test_lines,
        'ratio': round(ratio, 2)
    }

def update_readme_with_results(test_results):
    """更新README.md文件中的测试结果"""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    
    # 读取README.md文件
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 计算代码比例
    code_ratio = calculate_code_ratio()
    
    # 更新测试用例统计表格（统计信息部分）
    test_case_statistics = f"""| 测试类型 | 测试文件 | 测试用例数 | 代码行数 |
|----------|----------|------------|----------|
| 单元测试 | test_basic_functions.py | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestBasicFunctions'])} | {count_lines(os.path.join(os.path.dirname(__file__), 'test_basic_functions.py'))} |
| 单元测试 | test_llm_functions.py | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestLLMFunctions'])} | {count_lines(os.path.join(os.path.dirname(__file__), 'test_llm_functions.py'))} |
| 系统测试 | test_system_integration.py | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestSystemIntegration'])} | {count_lines(os.path.join(os.path.dirname(__file__), 'test_system_integration.py'))} |
| 验收测试 | test_acceptance.py | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestAcceptance'])} | {count_lines(os.path.join(os.path.dirname(__file__), 'test_acceptance.py'))} |
| 角色认证测试 | test_role_auth.py | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestRoleAuth'])} | {count_lines(os.path.join(os.path.dirname(__file__), 'test_role_auth.py'))} |
| 安全测试 | test_security.py | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestSecurity'])} | {count_lines(os.path.join(os.path.dirname(__file__), 'test_security.py'))} |
| 性能测试 | test_performance.py | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestPerformance'])} | {count_lines(os.path.join(os.path.dirname(__file__), 'test_performance.py'))} |
| **总计** | **7个文件** | **{test_results['total']}** | **{code_ratio['test_lines']}** |"""
    
    # 更新代码覆盖率分析表格（统计信息部分）
    code_coverage_table = f"""| 类别 | 行数 | 占比 |
|------|------|------|
| 应用功能代码 | {code_ratio['app_lines']} | - |
| 测试代码 | {code_ratio['test_lines']} | - |
| **测试代码覆盖率比例** | - | **{code_ratio['ratio']}:1** |"""
    
    # 更新测试结果统计表格（测试结果可视化部分）
    test_results_table = f"""| 测试类型 | 测试文件 | 测试用例数 | 通过数 | 失败数 | 错误数 | 通过率 |
|----------|----------|------------|--------|--------|--------|--------|
| 单元测试 | test_basic_functions.py | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestBasicFunctions'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestBasicFunctions' and r['status'] == 'passed'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestBasicFunctions' and r['status'] == 'failed'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestBasicFunctions' and r['status'] == 'error'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestBasicFunctions' and r['status'] == 'passed']) / len([r for r in test_results['test_details'] if r['class_name'] == 'TestBasicFunctions']) * 100:.1f}% |
| 单元测试 | test_llm_functions.py | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestLLMFunctions'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestLLMFunctions' and r['status'] == 'passed'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestLLMFunctions' and r['status'] == 'failed'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestLLMFunctions' and r['status'] == 'error'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestLLMFunctions' and r['status'] == 'passed']) / len([r for r in test_results['test_details'] if r['class_name'] == 'TestLLMFunctions']) * 100:.1f}% |
| 系统测试 | test_system_integration.py | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestSystemIntegration'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestSystemIntegration' and r['status'] == 'passed'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestSystemIntegration' and r['status'] == 'failed'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestSystemIntegration' and r['status'] == 'error'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestSystemIntegration' and r['status'] == 'passed']) / len([r for r in test_results['test_details'] if r['class_name'] == 'TestSystemIntegration']) * 100:.1f}% |
| 验收测试 | test_acceptance.py | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestAcceptance'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestAcceptance' and r['status'] == 'passed'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestAcceptance' and r['status'] == 'failed'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestAcceptance' and r['status'] == 'error'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestAcceptance' and r['status'] == 'passed']) / len([r for r in test_results['test_details'] if r['class_name'] == 'TestAcceptance']) * 100:.1f}% |
| 角色认证测试 | test_role_auth.py | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestRoleAuth'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestRoleAuth' and r['status'] == 'passed'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestRoleAuth' and r['status'] == 'failed'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestRoleAuth' and r['status'] == 'error'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestRoleAuth' and r['status'] == 'passed']) / len([r for r in test_results['test_details'] if r['class_name'] == 'TestRoleAuth']) * 100:.1f}% |
| 安全测试 | test_security.py | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestSecurity'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestSecurity' and r['status'] == 'passed'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestSecurity' and r['status'] == 'failed'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestSecurity' and r['status'] == 'error'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestSecurity' and r['status'] == 'passed']) / len([r for r in test_results['test_details'] if r['class_name'] == 'TestSecurity']) * 100:.1f}% |
| 性能测试 | test_performance.py | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestPerformance'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestPerformance' and r['status'] == 'passed'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestPerformance' and r['status'] == 'failed'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestPerformance' and r['status'] == 'error'])} | {len([r for r in test_results['test_details'] if r['class_name'] == 'TestPerformance' and r['status'] == 'passed']) / len([r for r in test_results['test_details'] if r['class_name'] == 'TestPerformance']) * 100:.1f}% |
| **总计** | **-** | **{test_results['total']}** | **{test_results['passed']}** | **{test_results['failed']}** | **{test_results['errors']}** | **{test_results['success_rate']:.1f}%** |"""
    
    # 计算每个测试文件的时间统计
    test_times = {}
    for test in test_results['test_details']:
        class_name = test['class_name']
        if class_name == 'TestBasicFunctions':
            file_name = 'test_basic_functions.py'
        elif class_name == 'TestLLMFunctions':
            file_name = 'test_llm_functions.py'
        elif class_name == 'TestSystemIntegration':
            file_name = 'test_system_integration.py'
        elif class_name == 'TestAcceptance':
            file_name = 'test_acceptance.py'
        elif class_name == 'TestRoleAuth':
            file_name = 'test_role_auth.py'
        elif class_name == 'TestSecurity':
            file_name = 'test_security.py'
        elif class_name == 'TestPerformance':
            file_name = 'test_performance.py'
        else:
            continue
        
        if file_name not in test_times:
            test_times[file_name] = {'total_time': 0.0, 'test_count': 0}
        
        test_times[file_name]['total_time'] += test.get('duration', 0.0)
        test_times[file_name]['test_count'] += 1
    
    # 更新测试时间统计表格
    test_time_rows = []
    total_time = 0.0
    total_tests = 0
    
    for file_name in [
        'test_basic_functions.py',
        'test_llm_functions.py',
        'test_system_integration.py',
        'test_acceptance.py',
        'test_role_auth.py',
        'test_security.py',
        'test_performance.py',
    ]:
        if file_name in test_times:
            stats = test_times[file_name]
            avg_time = stats['total_time'] / stats['test_count'] if stats['test_count'] > 0 else 0.0
            test_time_rows.append(f"| {file_name} | {stats['total_time']:.3f}秒 | {avg_time:.3f}秒 |")
            total_time += stats['total_time']
            total_tests += stats['test_count']
    
    avg_total_time = total_time / total_tests if total_tests > 0 else 0.0
    test_time_rows.append(f"| **总计** | **{total_time:.3f}秒** | **{avg_total_time:.3f}秒** |")
    
    test_time_table = "\n".join(test_time_rows)
    
    # 替换测试用例统计表格
    start_marker = "### 测试用例统计\n\n|"
    end_marker = "### 代码覆盖率分析"
    
    if start_marker in content and end_marker in content:
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        if start_idx != -1 and end_idx != -1:
            new_content = content[:start_idx] + f"### 测试用例统计\n\n{test_case_statistics}\n\n" + content[end_idx:]
            content = new_content
    
    # 替换代码覆盖率分析表格
    start_marker = "### 代码覆盖率分析\n\n|"
    end_marker = "## 🧪 单元测试设计介绍"
    
    if start_marker in content and end_marker in content:
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        if start_idx != -1 and end_idx != -1:
            new_content = content[:start_idx] + f"### 代码覆盖率分析\n\n{code_coverage_table}\n\n" + content[end_idx:]
            content = new_content
    
    # 替换测试结果可视化部分（删除该标题后所有内容，填入新内容）
    start_marker = "## 📊 测试结果可视化"
    
    if start_marker in content:
        start_idx = content.find(start_marker)
        # 查找下一个一级标题或文件结束
        next_section = content.find("\n## ", start_idx + 1)
        if next_section == -1:
            # 如果没有下一个一级标题，就到文件末尾
            end_idx = len(content)
        else:
            end_idx = next_section
        
        # 构建新的测试结果可视化内容
        test_results_content = f"""## 📊 测试结果可视化

### 测试结果统计

{test_results_table}

### 测试时间统计

| 测试文件 | 测试时间 | 平均每个测试用例时间 |
|----------|----------|----------------------|
{test_time_table}
"""
        
        # 如果有失败的测试，添加失败详情
        failed_tests = [r for r in test_results['test_details'] if r['status'] in ['failed', 'error']]
        if failed_tests:
            failure_details = "\n\n## ❌ 测试失败详情\n\n"
            for test in failed_tests:
                failure_details += f"### {test['class_name']}.{test['test_name']}\n\n"
                failure_details += f"**状态**: {'失败' if test['status'] == 'failed' else '错误'}\n\n"
                if test['message']:
                    failure_details += f"**错误信息**:\n```\n{test['message'][:500]}...\n```\n\n"
            test_results_content += failure_details
        
        # 替换内容
        new_content = content[:start_idx].rstrip() + "\n\n" + test_results_content + content[end_idx:].lstrip("\n")
        content = new_content
    
    # 保存更新后的README.md
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"README.md已更新，测试结果已写入")

def generate_report():
    """生成测试报告（已改为更新README.md）"""
    from test_suite import run_all_tests
    test_results = run_all_tests()
    update_readme_with_results(test_results)
    return True

if __name__ == '__main__':
    generate_report()
