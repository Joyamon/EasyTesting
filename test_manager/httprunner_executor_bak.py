import json
import time
import logging
import requests
from urllib.parse import urljoin

# 尝试导入 HTTPRunner，如果失败则记录错误但不中断执行
# try:
#     import httprunner
#
#     # 尝试多种方式获取 HTTPRunner 版本
#     if hasattr(httprunner, "__version__"):
#         HTTPRUNNER_VERSION = httprunner.__version__
#     elif hasattr(httprunner, "__version"):
#         HTTPRUNNER_VERSION = httprunner.__version
#     elif hasattr(httprunner, "version"):
#         HTTPRUNNER_VERSION = httprunner.version
#     else:
#         # 尝试从包信息获取版本
#         try:
#             import pkg_resources
#
#             HTTPRUNNER_VERSION = pkg_resources.get_distribution("httprunner").version
#         except:
#             HTTPRUNNER_VERSION = "unknown"
#
#     # 尝试导入 HttpRunner 类
#     try:
#         from httprunner.runner import HttpRunner
#
#         HTTPRUNNER_AVAILABLE = True
#     except ImportError:
#         # 尝试其他可能的导入路径
#         try:
#             from httprunner.api import HttpRunner
#
#             HTTPRUNNER_AVAILABLE = True
#         except ImportError:
#             HTTPRUNNER_AVAILABLE = False
# except ImportError:
#     HTTPRUNNER_AVAILABLE = False
#     HTTPRUNNER_VERSION = "not installed"

logger = logging.getLogger(__name__)
# logger.info(f"HTTPRunner version: {HTTPRUNNER_VERSION}, Available: {HTTPRUNNER_AVAILABLE}")


def execute_test_case(test_case, environment):
    """
    Execute a single test case using direct HTTP request
    """
    try:
        # 记录测试开始信息
        logger.info(
            f"Executing test case: {test_case.name} (ID: {test_case.id}) with environment: {environment.name} (ID: {environment.id})")
        logger.info(
            f"Request method: {test_case.request_method}, URL: {test_case.request_url}, Body format: {test_case.request_body_format}")

        start_time = time.time()

        # 直接使用 HTTP 请求执行测试
        result = _execute_with_requests(test_case, environment)

        # 计算响应时间
        end_time = time.time()
        result["response_time"] = (end_time - start_time) * 1000  # 转换为毫秒

        return result

    except Exception as e:
        logger.exception(f"Error executing test case: {e}")
        return {
            "status": "error",
            "response_time": 0,
            "response_status_code": None,
            "response_headers": {},
            "response_body": {},
            "error_message": str(e)
        }


def _execute_with_requests(test_case, environment):
    """
    Execute test case using direct HTTP requests
    """
    try:
        # 构建完整 URL
        base_url = environment.base_url.rstrip('/')
        request_url = test_case.request_url.lstrip('/')
        full_url = urljoin(f"{base_url}/", request_url)

        logger.info(f"Executing direct HTTP request to: {full_url}")

        # 准备请求参数
        headers = test_case.request_headers.copy() if test_case.request_headers else {}
        kwargs = {
            "headers": headers,
            "timeout": 30
        }

        # 根据请求体格式处理请求数据
        if test_case.request_body and test_case.request_method in ['POST', 'PUT', 'PATCH']:
            if test_case.request_body_format == 'json':
                # 确保设置了正确的 Content-Type
                if 'Content-Type' not in headers:
                    kwargs["headers"]["Content-Type"] = "application/json"
                kwargs["json"] = test_case.request_body
                logger.debug(f"Request body (JSON): {json.dumps(test_case.request_body)}")
            elif test_case.request_body_format == 'form-data':
                # 确保设置了正确的 Content-Type
                if 'Content-Type' not in headers:
                    kwargs["headers"]["Content-Type"] = "application/x-www-form-urlencoded"
                kwargs["data"] = test_case.request_body
                logger.debug(f"Request body (form-data): {test_case.request_body}")

        # 发送请求
        logger.debug(f"Request method: {test_case.request_method}, Headers: {kwargs['headers']}")
        response = requests.request(
            method=test_case.request_method,
            url=full_url,
            **kwargs
        )

        # 处理响应
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")

        try:
            response_body = response.json()
            logger.debug("Response body parsed as JSON")
        except ValueError:
            response_body = {"content": response.text}
            logger.debug("Response body parsed as text")

        # 检查状态码是否符合预期
        success = response.status_code == test_case.expected_status_code

        # 验证其他规则
        validation_errors = []
        for rule in test_case.validation_rules:
            # 简单实现一些基本的验证规则
            if "eq" in rule:
                path, expected = rule["eq"]
                # 简化的 JSONPath 实现，仅支持基本路径
                if path == "status_code":
                    actual = response.status_code
                elif path.startswith("$."):
                    # 非常简化的 JSONPath 解析
                    parts = path[2:].split('.')
                    actual = response_body
                    try:
                        for part in parts:
                            if isinstance(actual, dict):
                                actual = actual.get(part)
                            else:
                                actual = None
                                break
                    except:
                        actual = None
                else:
                    actual = None

                if actual != expected:
                    validation_errors.append(f"Validation failed: expected {path} to be {expected}, got {actual}")
                    success = False

            # 添加对 contains 验证规则的支持
            elif "contains" in rule:
                path, expected = rule["contains"]
                if path == "content" or path == "text":
                    # 检查响应文本是否包含预期字符串
                    actual = response.text
                    if expected not in actual:
                        validation_errors.append(f"Validation failed: expected response to contain '{expected}'")
                        success = False
                elif path.startswith("$."):
                    # 简化的 JSONPath 解析
                    parts = path[2:].split('.')
                    actual = response_body
                    try:
                        for part in parts:
                            if isinstance(actual, dict):
                                actual = actual.get(part)
                            else:
                                actual = None
                                break

                        if actual is None or expected not in str(actual):
                            validation_errors.append(f"Validation failed: expected {path} to contain '{expected}'")
                            success = False
                    except:
                        validation_errors.append(f"Validation failed: could not evaluate {path}")
                        success = False

        # 确定测试状态
        status = "passed" if success else "failed"
        error_message = "\n".join(validation_errors) if validation_errors else ""

        return {
            "status": status,
            "response_status_code": response.status_code,
            "response_headers": dict(response.headers),
            "response_body": response_body,
            "error_message": error_message
        }

    except requests.RequestException as e:
        logger.exception(f"HTTP request error: {e}")
        return {
            "status": "error",
            "response_status_code": None,
            "response_headers": {},
            "response_body": {},
            "error_message": f"HTTP request error: {str(e)}"
        }
    except Exception as e:
        logger.exception(f"Unexpected error in direct HTTP request: {e}")
        return {
            "status": "error",
            "response_status_code": None,
            "response_headers": {},
            "response_body": {},
            "error_message": f"Unexpected error: {str(e)}"
        }


def execute_test_suite(test_suite, environment):
    """
    Execute a test suite (multiple test cases) using direct HTTP requests
    """
    results = []

    # 获取套件中的所有测试用例，按顺序排列
    test_suite_cases = test_suite.testsuitecase_set.all().order_by('order')

    logger.info(
        f"Executing test suite: {test_suite.name} (ID: {test_suite.id}) with {test_suite_cases.count()} test cases")

    for test_suite_case in test_suite_cases:
        test_case = test_suite_case.test_case
        logger.info(f"Executing test case {test_case.name} (ID: {test_case.id}) from suite")

        result = execute_test_case(test_case, environment)
        result['test_case_id'] = test_case.id
        results.append(result)

        logger.info(f"Test case {test_case.name} execution result: {result['status']}")

    logger.info(
        f"Test suite execution completed. Total: {len(results)}, Passed: {sum(1 for r in results if r['status'] == 'passed')}")

    return results
