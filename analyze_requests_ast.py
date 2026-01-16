# -*- coding: utf-8 -*-
import ast
import os
import sys
from collections import defaultdict

# 设置requests源代码目录
src_dir = os.path.join(os.path.dirname(__file__), 'requests', 'requests', 'src', 'requests')

# 确保目录存在
if not os.path.exists(src_dir):
    print(f"错误: 在 {src_dir} 未找到源代码目录")
    sys.exit(1)

# 存储分析结果的字典
analysis_results = {
    'total_files': 0,
    'total_lines': 0,
    'classes': defaultdict(list),  # 类名 -> [文件路径]
    'functions': defaultdict(list),  # 函数名 -> [文件路径]
    'class_inheritance': {},  # 类名 -> 父类列表
    'function_calls': defaultdict(int),  # 函数调用次数统计
    'imports': defaultdict(int),  # 导入模块统计
    'top_level_functions': defaultdict(list),  # 顶层函数 -> [文件路径]
    'method_count': defaultdict(int),  # 类 -> 方法数量
    'module_dependencies': defaultdict(set),  # 模块 -> 依赖的模块
}


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
    # 获取相对路径用于报告
    rel_path = os.path.relpath(file_path, src_dir)

    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 统计行数
    analysis_results['total_lines'] += len(content.split('\n'))

    # 解析AST
    try:
        tree = ast.parse(content, filename=rel_path)
        # 为节点添加父引用
        add_parent_references(tree)
    except SyntaxError as e:
        print(f"在 {rel_path} 中发现语法错误: {e}")
        return

    # 遍历AST节点
    class_defs = []

    for node in ast.walk(tree):
        # 分析导入
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for name in node.names:
                    module = name.name.split('.')[0]
                    analysis_results['imports'][module] += 1
                    analysis_results['module_dependencies'][rel_path].add(module)
            else:
                if node.module:
                    module = node.module.split('.')[0]
                    analysis_results['imports'][module] += 1
                    analysis_results['module_dependencies'][rel_path].add(module)

        # 分析类定义
        elif isinstance(node, ast.ClassDef):
            class_defs.append(node)
            analysis_results['classes'][node.name].append(rel_path)

            # 记录继承关系
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(f"{base.value.id}.{base.attr}")
            analysis_results['class_inheritance'][node.name] = bases

        # 分析函数/方法定义
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            func_name = node.name
            is_async = isinstance(node, ast.AsyncFunctionDef)

            # 检查是否是类方法
            parent = None
            for ancestor in ast.walk_up(node):
                if isinstance(ancestor, ast.ClassDef):
                    parent = ancestor.name
                    break

            if parent:
                # 是类方法
                analysis_results['method_count'][parent] += 1
            else:
                # 是顶层函数
                analysis_results['top_level_functions'][func_name].append(rel_path)

            analysis_results['functions'][func_name].append(rel_path)

        # 分析函数调用
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                analysis_results['function_calls'][func_name] += 1
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    func_name = f"{node.func.value.id}.{node.func.attr}"
                    analysis_results['function_calls'][func_name] += 1

    # 增加文件计数
    analysis_results['total_files'] += 1


# 为AST节点添加walk_up方法以查找父节点
def walk_up(node):
    """生成给定节点的所有父节点"""
    while hasattr(node, 'parent') and node.parent:
        yield node.parent
        node = node.parent


# 在遍历AST之前添加父引用
def add_parent_references(tree):
    """为每个节点添加parent属性"""
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node
    return tree


# 扩展ast模块以包含walk_up方法
ast.walk_up = walk_up


# 主分析函数
def main():
    print("开始对requests库进行AST分析...")

    # 获取所有Python文件
    python_files = get_python_files(src_dir)

    print(f"找到 {len(python_files)} 个Python文件需要分析")

    # 分析每个文件
    for file_path in python_files:
        analyze_file(file_path)

    # 输出分析结果
    print("\n" + "=" * 60)
    print("REQUESTS库AST分析结果")
    print("=" * 60)

    print(f"\n1. 基本统计:")
    print(f"   总文件数: {analysis_results['total_files']}")
    print(f"   总行数: {analysis_results['total_lines']}")

    print(f"\n2. 类定义 (共 {len(analysis_results['classes'])} 个类):")
    for cls, files in sorted(analysis_results['classes'].items()):
        inheritance = analysis_results['class_inheritance'].get(cls, [])
        inheritance_str = f" -> {', '.join(inheritance)}" if inheritance else ""
        print(f"   {cls}{inheritance_str} 在 {', '.join(files)}")

    print(f"\n3. 顶层函数 (共 {len(analysis_results['top_level_functions'])} 个函数):")
    for func, files in sorted(analysis_results['top_level_functions'].items()):
        print(f"   {func} 在 {', '.join(files)}")

    print(f"\n4. 类方法数量:")
    for cls, count in sorted(analysis_results['method_count'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {cls}: {count} 个方法")

    print(f"\n5. 最常见的函数调用:")
    for func, count in sorted(analysis_results['function_calls'].items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"   {func}: {count} 次调用")

    print(f"\n6. 导入统计:")
    for module, count in sorted(analysis_results['imports'].items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"   {module}: {count} 次导入")

    print(f"\n7. 模块依赖:")
    for module, dependencies in sorted(analysis_results['module_dependencies'].items()):
        if dependencies:
            print(f"   {module} 依赖于: {', '.join(sorted(dependencies))}")

    print(f"\n" + "=" * 60)
    print("分析完成")
    print("=" * 60)


if __name__ == "__main__":
    main()

