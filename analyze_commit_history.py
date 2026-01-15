#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析requests库的提交历史
"""

import os
import re
import subprocess
from collections import defaultdict, Counter
from datetime import datetime

# 设置仓库路径
git_repo_path = os.path.join(os.path.dirname(__file__), 'requests', 'requests')

# 确保是git仓库目录
if not os.path.exists(os.path.join(git_repo_path, '.git')):
    print(f"错误: {git_repo_path} 不是一个git仓库")
    exit(1)


def run_git_command(cmd):
    """运行git命令并返回输出"""
    result = subprocess.run(cmd, cwd=git_repo_path, shell=True, capture_output=True,
                            text=True, encoding='utf-8')
    if result.returncode != 0:
        print(f"运行git命令出错: {cmd}")
        print(f"错误: {result.stderr}")
        return None
    return result.stdout


def get_commit_history():
    """获取完整的提交历史"""
    cmd = 'git log --pretty=format:"%h|%an|%ae|%ad|%s" --date=iso'
    output = run_git_command(cmd)
    if output is None:
        return []

    commits = []
    for line in output.strip().split('\n'):
        parts = line.split('|', 4)
        if len(parts) == 5:
            # 修复日期解析，处理特殊时区格式
            date_str = parts[3]
            try:
                # 尝试用固定格式解析
                commit_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S %z')
            except ValueError:
                # 如果失败，尝试另一种方法
                # 移除时区偏移，使用UTC
                date_str_no_tz = date_str.split(' ', 2)[0] + ' ' + date_str.split(' ', 2)[1]
                commit_date = datetime.strptime(date_str_no_tz, '%Y-%m-%d %H:%M:%S')

            commit = {
                'hash': parts[0],
                'author_name': parts[1],
                'author_email': parts[2],
                'date': commit_date,
                'message': parts[4]
            }
            commits.append(commit)
    return commits


def analyze_commits(commits):
    """分析提交数据"""
    if not commits:
        print("未找到提交记录")
        return

    total_commits = len(commits)
    print(f"总提交数: {total_commits}")
    print(f"首次提交: {commits[-1]['date']}")
    print(f"最近提交: {commits[0]['date']}")
    print(f"时间跨度: {commits[0]['date'] - commits[-1]['date']}")

    # 1. 统计开发者贡献
    author_commits = Counter()
    author_emails = defaultdict(set)

    for commit in commits:
        author_commits[commit['author_name']] += 1
        author_emails[commit['author_name']].add(commit['author_email'])

    print(f"\n1. 开发者贡献 (前20名):")
    print(f"{'作者':<30} {'提交数':<10} {'邮箱':<15}")
    print("-" * 60)
    for author, count in author_commits.most_common(20):
        emails = author_emails[author]
        print(f"{author:<30} {count:<10} {', '.join(emails):<15}")

    # 2. 提交频率分析
    print(f"\n2. 提交频率:")

    # 年度统计
    yearly = defaultdict(int)
    for commit in commits:
        yearly[commit['date'].year] += 1

    print(f"\n按年统计:")
    print(f"{'年份':<10} {'提交数':<10}")
    print("-" * 20)
    for year in sorted(yearly.keys()):
        print(f"{year:<10} {yearly[year]:<10}")

    # 月度统计（最近24个月）
    monthly = defaultdict(int)
    for commit in commits:
        month_key = f"{commit['date'].year}-{commit['date'].month:02d}"
        monthly[month_key] += 1

    print(f"\n按月统计（最近24个月）:")
    print(f"{'月份':<12} {'提交数':<10}")
    print("-" * 25)
    sorted_months = sorted(monthly.keys(), reverse=True)[:24][::-1]
    for month in sorted_months:
        print(f"{month:<12} {monthly[month]:<10}")

    # 3. 提交信息关键词分析
    print(f"\n3. 提交信息关键词（前20名）:")
    keywords = []
    for commit in commits:
        # 提取单词，忽略常见单词和短单词
        words = re.findall(r'\b\w{3,}\b', commit['message'].lower())
        keywords.extend(words)

    # 忽略常见单词
    ignore_words = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'into', 'onto', 'but', 'not', 'are', 'was',
                    'were', 'you', 'your', 'our', 'we', 'they', 'them', 'their', 'it', 'its', 'by', 'in', 'on', 'to',
                    'of', 'at', 'as', 'is', 'if', 'can', 'will', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
                    'did', 'than', 'then', 'when', 'where', 'which', 'who', 'whom', 'whose', 'why', 'how', 'what',
                    'any', 'all', 'more', 'most', 'some', 'such', 'each', 'every', 'other', 'another', 'no', 'yes',
                    'up', 'down', 'out', 'over', 'under', 'above', 'below', 'through', 'across', 'about', 'against',
                    'among', 'between', 'during', 'before', 'after', 'because', 'since', 'while', 'until', 'unless',
                    'though', 'although', 'however', 'therefore', 'hence', 'thus', 'so', 'too', 'very', 'only', 'just',
                    'now', 'new', 'old', 'good', 'bad', 'better', 'worse', 'best', 'worst', 'first', 'last', 'next',
                    'previous', 'current', 'future', 'past', 'present', 'back', 'front', 'left', 'right', 'top',
                    'bottom', 'middle', 'high', 'low', 'higher', 'lower', 'big', 'small', 'larger', 'smaller', 'long',
                    'short', 'longer', 'shorter', 'wide', 'narrow', 'wider', 'narrower', 'deep', 'shallow', 'deeper',
                    'shallower', 'fast', 'slow', 'faster', 'slower', 'quick', 'quickly', 'slow', 'slowly'}

    filtered_keywords = [word for word in keywords if word not in ignore_words]
    keyword_counts = Counter(filtered_keywords)

    print(f"{'关键词':<15} {'出现次数':<10}")
    print("-" * 25)
    for keyword, count in keyword_counts.most_common(20):
        print(f"{keyword:<15} {count:<10}")

    # 4. 提交类型分析（基于提交信息前缀）
    print(f"\n4. 提交类型:")
    commit_types = Counter()
    for commit in commits:
        # 查找常见的提交类型前缀
        match = re.match(r'^(\w+):', commit['message'])
        if match:
            commit_types[match.group(1).lower()] += 1

    print(f"{'类型':<15} {'数量':<10} {'百分比':<10}")
    print("-" * 35)
    for commit_type, count in commit_types.most_common(10):
        percentage = (count / total_commits) * 100
        print(f"{commit_type:<15} {count:<10} {percentage:.1f}%     ")

    # 5. 修复相关的提交
    print(f"\n5. 修复相关提交:")
    fix_words = {'fix', 'bug', 'issue', 'error', 'correct', 'repair', 'resolve', 'patch', 'fixes', 'fixed', 'fixing'}
    fix_commits = 0
    for commit in commits:
        commit_lower = commit['message'].lower()
        if any(word in commit_lower for word in fix_words):
            fix_commits += 1

    print(f"修复相关提交总数: {fix_commits} (占总提交数的 {(fix_commits / total_commits) * 100:.1f}%)")

    # 6. 最长连续提交
    print(f"\n6. 最长连续提交:")
    if not commits:
        print("未找到提交记录")
        return

    # 对日期进行排序，从最旧到最新
    sorted_dates = sorted(set(commit['date'].date() for commit in commits))

    if not sorted_dates:
        print("未找到提交日期")
        return

    longest_streak = 1
    current_streak = 1

    for i in range(1, len(sorted_dates)):
        day_diff = (sorted_dates[i] - sorted_dates[i - 1]).days
        if day_diff == 1:
            current_streak += 1
            if current_streak > longest_streak:
                longest_streak = current_streak
        else:
            current_streak = 1

    print(f"最长连续提交天数: {longest_streak} 天")


def main():
    """主函数"""
    print("正在分析requests库的提交历史...")

    # 获取提交历史
    commits = get_commit_history()

    if not commits:
        print("未找到提交记录")
        return

    print(f"找到 {len(commits)} 条提交记录")

    # 分析提交数据
    analyze_commits(commits)

    print(f"\n分析完成！")


if __name__ == "__main__":
    main()
