#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对requests库进行模糊测试
此脚本对requests库执行模糊测试，以识别潜在的安全漏洞
"""

# 确保我们使用已安装的requests模块
import requests
import random
import string
import time
import re
from collections import defaultdict
import logging
import threading
import concurrent.futures

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='fuzz_test_results.log'
)
logger = logging.getLogger(__name__)

# 创建控制台处理器用于即时输出
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class RequestsFuzzer:
    """用于对requests库进行模糊测试的类"""

    def __init__(self, target_url="http://httpbin.org/", max_requests=1000, max_threads=10):
        """使用目标URL和参数初始化模糊测试器"""
        self.target_url = target_url
        self.max_requests = max_requests
        self.max_threads = max_threads
        self.results = {
            'total_requests': 0,
            'success': 0,
            'errors': 0,
            'exceptions': defaultdict(int),
            'status_codes': defaultdict(int),
            'test_methods': defaultdict(int)
        }

    def generate_random_string(self, min_length=1, max_length=100, allowed_chars=None):
        """生成具有指定允许字符的随机字符串"""
        if allowed_chars is None:
            allowed_chars = string.printable
        length = random.randint(min_length, max_length)
        return ''.join(random.choice(allowed_chars) for _ in range(length))

    def generate_random_header_name(self, min_length=3, max_length=20):
        """生成符合HTTP标准的header名称"""
        allowed_chars = string.ascii_letters + string.digits + '-'
        length = random.randint(min_length, max_length)
        # 必须以字母开头
        name = random.choice(string.ascii_letters)
        name += ''.join(random.choice(allowed_chars) for _ in range(length - 1))
        # 移除末尾的连字符
        return name.rstrip('-')

    def generate_random_header_value(self, min_length=1, max_length=50):
        """生成符合HTTP标准的header值"""
        # 允许使用可打印字符，除了控制字符（换行符、回车符等）
        allowed_chars = ''.join(c for c in string.printable if not c.isspace() or c in [' ', '\t'])
        return self.generate_random_string(min_length, max_length, allowed_chars)

    def generate_url_safe_string(self, min_length=1, max_length=50):
        """生成URL安全的字符串"""
        allowed_chars = string.ascii_letters + string.digits + '-._~'
        return self.generate_random_string(min_length, max_length, allowed_chars)

    def generate_json_safe_string(self, min_length=1, max_length=50):
        """生成JSON安全的字符串"""
        allowed_chars = string.ascii_letters + string.digits + ' -_.,!@#$%^&*()_+'
        return self.generate_random_string(min_length, max_length, allowed_chars)

    def generate_random_url(self):
        """生成更合理的随机URL路径"""
        path_segments = []
        # 限制为0-3个路径段以提高成功率
        for _ in range(random.randint(0, 3)):
            segment = self.generate_url_safe_string(2, 15)
            if segment:  # 只添加非空段
                path_segments.append(segment)
        path = '/' + '/'.join(path_segments)
        return self.target_url.rstrip('/') + path

    def generate_random_headers(self, max_headers=10):
        """生成符合HTTP标准的随机headers"""
        headers = {}
        for _ in range(random.randint(0, max_headers)):
            key = self.generate_random_header_name()
            value = self.generate_random_header_value()
            headers[key] = value
        return headers

    def generate_random_params(self, max_params=10):
        """生成随机查询参数"""
        params = {}
        for _ in range(random.randint(0, max_params)):
            key = self.generate_url_safe_string(3, 20)
            value = self.generate_url_safe_string(1, 50)
            params[key] = value
        return params

    def generate_random_data(self):
        """为POST/PUT请求生成随机数据"""
        data_type = random.choice(['none', 'params', 'json', 'string'])

        if data_type == 'none':
            return None, None
        elif data_type == 'params':
            return self.generate_random_params(), None
        elif data_type == 'json':
            # 生成JSON安全的数据
            json_data = {}
            for _ in range(random.randint(0, 5)):
                key = self.generate_json_safe_string(3, 20)
                value = self.generate_json_safe_string(1, 50)
                json_data[key] = value
            return None, json_data
        else:
            return self.generate_json_safe_string(1, 500), None

    def get_random_http_method(self):
        """获取随机HTTP方法"""
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH']
        return random.choice(methods)

    def test_http_request(self):
        """使用优化的模糊参数测试单个HTTP请求"""
        self.results['total_requests'] += 1

        # 生成优化的模糊参数
        method = self.get_random_http_method()
        url = self.generate_random_url()
        headers = self.generate_random_headers()
        params = self.generate_random_params()
        data, json_data = self.generate_random_data()
        timeout = 3  # 固定合理的超时时间

        retries = 1  # 超时时重试一次
        for attempt in range(retries + 1):
            try:
                if method == 'GET':
                    response = requests.get(
                        url,
                        headers=headers,
                        params=params,
                        timeout=timeout
                    )
                elif method == 'POST':
                    response = requests.post(
                        url,
                        headers=headers,
                        params=params,
                        data=data,
                        json=json_data,
                        timeout=timeout
                    )
                elif method == 'PUT':
                    response = requests.put(
                        url,
                        headers=headers,
                        params=params,
                        data=data,
                        json=json_data,
                        timeout=timeout
                    )
                elif method == 'DELETE':
                    response = requests.delete(
                        url,
                        headers=headers,
                        params=params,
                        timeout=timeout
                    )
                elif method == 'HEAD':
                    response = requests.head(
                        url,
                        headers=headers,
                        params=params,
                        timeout=timeout
                    )
                elif method == 'OPTIONS':
                    response = requests.options(
                        url,
                        headers=headers,
                        timeout=timeout
                    )
                elif method == 'PATCH':
                    response = requests.patch(
                        url,
                        headers=headers,
                        params=params,
                        data=data,
                        json=json_data,
                        timeout=timeout
                    )
                else:
                    logger.warning(f"未知的HTTP方法: {method}")
                    return

                # 记录成功响应
                self.results['success'] += 1
                self.results['status_codes'][response.status_code] += 1
                self.results['test_methods'][method] += 1

                # 测试响应解析
                try:
                    if response.text:
                        response.text
                        response.content
                        if 'application/json' in response.headers.get('Content-Type', ''):
                            response.json()
                except Exception as e:
                    logger.error(f"响应解析错误: {type(e).__name__}: {e}")
                    self.results['errors'] += 1
                    self.results['exceptions'][type(e).__name__] += 1

                break  # 成功，退出重试循环

            except requests.exceptions.Timeout:
                if attempt < retries:
                    logger.debug(f"超时，正在重试 ({attempt + 1}/{retries + 1})")
                    time.sleep(0.1)
                else:
                    logger.debug(f"在{retries + 1}次尝试后最终超时")
                    self.results['errors'] += 1
                    self.results['exceptions']['Timeout'] += 1
            except Exception as e:
                # 记录其他异常
                self.results['errors'] += 1
                self.results['exceptions'][type(e).__name__] += 1
                logger.debug(f"异常: {type(e).__name__}: {e}")
                break  # 非超时异常不重试

    def test_session_management(self):
        """使用优化的模糊数据测试会话管理"""
        self.results['total_requests'] += 1

        try:
            session = requests.Session()

            # 使用有效的headers配置会话
            session.headers.update(self.generate_random_headers())

            # 使用同一会话进行多次请求
            for _ in range(random.randint(1, 3)):  # 减少到每个会话1-3个请求
                url = self.generate_random_url()
                method = self.get_random_http_method()

                if method == 'GET':
                    session.get(url, params=self.generate_random_params(), timeout=3)
                elif method == 'POST':
                    data, json_data = self.generate_random_data()
                    session.post(url, data=data, json=json_data, params=self.generate_random_params(), timeout=3)

            self.results['success'] += 1
            self.results['test_methods']['Session'] += 1

        except Exception as e:
            self.results['errors'] += 1
            self.results['exceptions'][type(e).__name__] += 1
            logger.error(f"会话管理错误: {type(e).__name__}: {e}")

    def run_fuzz_test(self):
        """使用优化参数运行模糊测试"""
        logger.info(f"开始在 {self.target_url} 上进行模糊测试")
        logger.info(f"要发送的总请求数: {self.max_requests}")
        logger.info(f"使用 {self.max_threads} 个线程")

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = []

            for _ in range(self.max_requests):
                # 调整测试类型权重以获得更好的成功率
                test_type = random.choices(['http_request', 'session'], weights=[70, 30])[0]

                if test_type == 'http_request':
                    futures.append(executor.submit(self.test_http_request))
                else:
                    futures.append(executor.submit(self.test_session_management))

            # 等待所有future完成
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Future异常: {e}")

        end_time = time.time()
        duration = end_time - start_time

        self.generate_report(duration)

    def generate_report(self, duration):
        """生成模糊测试报告"""
        logger.info("=" * 80)
        logger.info("模糊测试报告")
        logger.info("=" * 80)
        logger.info(f"目标URL: {self.target_url}")
        logger.info(f"总请求数: {self.results['total_requests']}")
        logger.info(f"成功请求数: {self.results['success']}")
        logger.info(f"错误请求数: {self.results['errors']}")
        logger.info(f"成功率: {self.results['success'] / self.results['total_requests'] * 100:.1f}%")
        logger.info(f"持续时间: {duration:.2f} 秒")
        logger.info(f"每秒请求数: {self.results['total_requests'] / duration:.2f}")

        logger.info("\n测试的HTTP方法:")
        for method, count in sorted(self.results['test_methods'].items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {method}: {count} 个请求")

        logger.info("\n响应状态码:")
        for status, count in sorted(self.results['status_codes'].items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {status}: {count} 个响应")

        logger.info("\n遇到的异常:")
        for exception, count in sorted(self.results['exceptions'].items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {exception}: {count} 次")

        logger.info("\n" + "=" * 80)
        logger.info("模糊测试完成")
        logger.info("=" * 80)


if __name__ == "__main__":
    # 使用优化设置创建模糊测试器实例
    fuzzer = RequestsFuzzer(
        target_url="http://httpbin.org/",
        max_requests=1000,
        max_threads=10
    )

    # 运行模糊测试
    fuzzer.run_fuzz_test()
