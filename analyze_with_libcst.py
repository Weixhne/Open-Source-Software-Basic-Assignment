#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用libcst对requests库进行深度静态分析
"""

import os
import sys
import libcst as cst
from collections import defaultdict, Counter

# 设置requests源代码目录
src_dir = os.path.join(os.path.dirname(__file__), 'requests', 'requests', 'src', 'requests')

# 确保目录存在
if not os.path.exists(src_dir):
    print(f"错误: 在 {src_dir} 未找到源代码目录")
    sys.exit(1)

# 分析结果
analysis_results = {
    'total_files': 0,
    'total_lines': 0,
    'function_complexity': defaultdict(list),  # 函数名 -> [复杂度分数]
    'class_method_counts': defaultdict(int),  # 类名 -> 方法数量
    'function_parameter_counts': defaultdict(int),  # 参数数量 -> 频率
    'decorator_usage': Counter(),  # 装饰器名 -> 使用次数
    'imports': Counter(),  # 导入路径 -> 计数
    'code_patterns': defaultdict(int),  # 模式名 -> 出现次数
    'variable_names': Counter(),  # 变量名 -> 使用次数
    'string_literals': Counter(),  # 常见字符串字面量 -> 出现次数
    'exception_handling': Counter(),  # 异常类型 -> 出现次数
}


class RequestAnalyzer(cst.CSTVisitor):
    """用于分析requests代码模式的自定义访问器"""

    def __init__(self):
        super().__init__()
        self.current_class = None  # 当前类名
        self.current_function = None  # 当前函数名
        self.if_depth = 0  # if语句嵌套深度
        self.for_depth = 0  # for循环嵌套深度
        self.while_depth = 0  # while循环嵌套深度

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        """访问类定义节点"""
        self.current_class = node.name.value

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        """离开类定义节点"""
        self.current_class = None

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        """访问函数定义节点"""
        self.current_function = node.name.value

        # 统计参数数量
        param_count = len(node.params.params)
        analysis_results['function_parameter_counts'][param_count] += 1

        # 统计装饰器使用
        for decorator in node.decorators:
            if isinstance(decorator.decorator, cst.Name):
                decorator_name = decorator.decorator.value
            elif isinstance(decorator.decorator, cst.Attribute):
                decorator_name = f"{decorator.decorator.value.value}.{decorator.decorator.attr.value}"
            else:
                decorator_name = "未知"
            analysis_results['decorator_usage'][decorator_name] += 1

        # 如果在类中，增加方法计数
        if self.current_class:
            analysis_results['class_method_counts'][self.current_class] += 1

    def leave_FunctionDef(self, node: cst.FunctionDef) -> None:
        """离开函数定义节点"""
        self.current_function = None

    def visit_Import(self, node: cst.Import) -> None:
        """访问导入节点"""
        for name in node.names:
            import_path = name.evaluated_name
            analysis_results['imports'][import_path] += 1

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        """访问from导入节点"""
        if node.module:
            module_name = node.module.value
            for name in node.names:
                import_path = f"{module_name}.{name.evaluated_name}"
                analysis_results['imports'][import_path] += 1

    def visit_If(self, node: cst.If) -> None:
        """访问if语句节点"""
        self.if_depth += 1

    def leave_If(self, node: cst.If) -> None:
        """离开if语句节点"""
        self.if_depth -= 1

    def visit_For(self, node: cst.For) -> None:
        """访问for循环节点"""
        self.for_depth += 1

    def leave_For(self, node: cst.For) -> None:
        """离开for循环节点"""
        self.for_depth -= 1

    def visit_While(self, node: cst.While) -> None:
        """访问while循环节点"""
        self.while_depth += 1

    def leave_While(self, node: cst.While) -> None:
        """离开while循环节点"""
        self.while_depth -= 1

    def visit_Name(self, node: cst.Name) -> None:
        """访问名称节点"""
        # 统计变量使用（排除关键字）
        import keyword
        if node.value not in keyword.kwlist:
            analysis_results['variable_names'][node.value] += 1

    def visit_SimpleString(self, node: cst.SimpleString) -> None:
        """访问字符串字面量节点"""
        # 统计常见字符串字面量
        string_value = node.evaluated_value
        if len(string_value) > 3 and len(string_value) < 50:
            analysis_results['string_literals'][string_value] += 1

    def visit_Raise(self, node: cst.Raise) -> None:
        """访问raise语句节点"""
        # 统计异常类型
        if isinstance(node.exc, cst.Call) and isinstance(node.exc.func, cst.Name):
            exception_type = node.exc.func.value
            analysis_results['exception_handling'][exception_type] += 1

    def visit_Try(self, node: cst.Try) -> None:
        """访问try语句节点"""
        # 统计except子句
        for handler in node.handlers:
            if handler.type and isinstance(handler.type, cst.Name):
                exception_type = handler.type.value
                analysis_results['exception_handling'][exception_type] += 1

    def visit_Call(self, node: cst.Call) -> None:
        """访问函数调用节点"""
        # 识别常见代码模式
        if isinstance(node.func, cst.Name):
            func_name = node.func.value

            # 检查常见模式
            if func_name == "print":
                analysis_results['code_patterns']['print语句'] += 1
            elif func_name == "len":
                analysis_results['code_patterns']['len调用'] += 1
            elif func_name == "str":
                analysis_results['code_patterns']['str调用'] += 1
            elif func_name == "int":
                analysis_results['code_patterns']['int调用'] += 1

        elif isinstance(node.func, cst.Attribute):
            # 检查对象方法调用
            if isinstance(node.func.value, cst.Name):
                obj_name = node.func.value.value
                method_name = node.func.attr.value

                # 检查常见模式，如requests.get, dict.items()
                if obj_name == "self" and method_name == "__init__":
                    analysis_results['code_patterns']['初始化方法'] += 1
                elif method_name in ["get", "post", "put", "delete"]:
                    analysis_results['code_patterns']['HTTP方法调用'] += 1
                elif method_name == "items":
                    analysis_results['code_patterns']['字典items调用'] += 1
                elif method_name == "keys":
                    analysis_results['code_patterns']['字典keys调用'] += 1
                elif method_name == "values":
                    analysis_results['code_patterns']['字典values调用'] += 1


# 获取目录中的所有Python文件
def get_python_files(directory):
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files


# 分析单个Python文件
def analyze_file(file_path):
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 更新行数统计
    analysis_results['total_lines'] += len(content.split('\n'))

    # 使用libcst解析
    try:
        module = cst.parse_module(content)
    except Exception as e:
        print(f"解析 {file_path} 时出错: {e}")
        return

    # 使用自定义访问器分析
    analyzer = RequestAnalyzer()
    module.visit(analyzer)

    # 增加文件计数
    analysis_results['total_files'] += 1


def main():
    """主函数"""
    print("开始使用libcst对requests库进行深度静态分析...")

    # 获取所有Python文件
    python_files = get_python_files(src_dir)

    print(f"找到 {len(python_files)} 个Python文件需要分析")

    # 分析每个文件
    for file_path in python_files:
        analyze_file(file_path)

    # 打印结果
    print("\n" + "=" * 60)
    print("REQUESTS库LIBCST分析结果")
    print("=" * 60)

    print(f"\n1. 基本统计:")
    print(f"   总文件数: {analysis_results['total_files']}")
    print(f"   总行数: {analysis_results['total_lines']}")

    print(f"\n2. 类方法数量（前15名）:")
    sorted_classes = sorted(analysis_results['class_method_counts'].items(),
                            key=lambda x: x[1], reverse=True)[:15]
    for cls, count in sorted_classes:
        print(f"   {cls}: {count} 个方法")

    print(f"\n3. 函数参数分布:")
    total_functions = sum(analysis_results['function_parameter_counts'].values())
    for param_count in sorted(analysis_results['function_parameter_counts'].keys()):
        count = analysis_results['function_parameter_counts'][param_count]
        percentage = (count / total_functions) * 100
        print(f"   {param_count} 个参数: {count} 个函数 ({percentage:.1f}%)")

    print(f"\n4. 装饰器使用（前10名）:")
    for decorator, count in analysis_results['decorator_usage'].most_common(10):
        print(f"   {decorator}: {count} 次使用")

    print(f"\n5. 主要导入（前15名）:")
    for import_path, count in analysis_results['imports'].most_common(15):
        print(f"   {import_path}: {count} 次导入")

    print(f"\n6. 代码模式:")
    for pattern, count in sorted(analysis_results['code_patterns'].items()):
        print(f"   {pattern}: {count}")

    print(f"\n7. 常见异常处理（前10名）:")
    for exception, count in analysis_results['exception_handling'].most_common(10):
        print(f"   {exception}: {count} 次出现")

    print(f"\n8. 常见变量名（前15名）:")
    for var_name, count in analysis_results['variable_names'].most_common(15):
        print(f"   {var_name}: {count} 次使用")

    print(f"\n9. 常见字符串字面量（前10名）:")
    for literal, count in analysis_results['string_literals'].most_common(10):
        print(f"   '{literal}': {count} 次出现")

    print(f"\n" + "=" * 60)
    print("分析完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
