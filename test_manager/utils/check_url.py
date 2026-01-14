import requests
import socket
import ssl
import datetime
from urllib.parse import urlparse
import time


def check_website_enhanced(url, timeout=10):
    """
    增强版网站检测，包含DNS解析、SSL证书等信息

    参数:
        url: 要检测的网站URL
        timeout: 超时时间（秒），默认10秒

    返回:
        dict: 包含详细检测结果的字典
    """
    result = {
        'url': url,
        'timestamp': datetime.datetime.now().isoformat(),
        'is_valid': False,
        'status_code': None,
        'response_time_ms': None,
        'errors': [],
        'details': {}
    }

    if not url:
        result['errors'].append("URL不能为空")
        return result

    # 1. 解析URL
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if not domain:
            result['errors'].append("无效的URL")
            return result

        result['details']['domain'] = domain
        result['details']['scheme'] = parsed_url.scheme
    except Exception as e:
        result['errors'].append(f"URL解析失败: {str(e)}")
        return result

    # 2. DNS解析检测
    try:
        start_time = time.time()
        ip_address = socket.gethostbyname(domain)
        dns_time = round((time.time() - start_time) * 1000, 2)
        result['details']['dns_resolution'] = {
            'ip_address': ip_address,
            'response_time_ms': dns_time
        }
    except socket.gaierror:
        result['errors'].append("DNS解析失败")
        return result
    except Exception as e:
        result['errors'].append(f"DNS解析错误: {str(e)}")
        return result

    # 3. HTTP/HTTPS连接检测
    try:
        start_time = time.time()

        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            verify=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
        )

        response_time = round((time.time() - start_time) * 1000, 2)

        result['status_code'] = response.status_code
        result['response_time_ms'] = response_time
        result['is_valid'] = response.status_code < 400

        # 添加更多详细信息
        result['details']['http_response'] = {
            'content_length': len(response.content),
            'content_type': response.headers.get('Content-Type', 'Unknown'),
            'server': response.headers.get('Server', 'Unknown'),
            'final_url': response.url
        }

        # 如果是HTTPS，添加SSL信息
        if parsed_url.scheme == 'https':
            try:
                cert = ssl.get_server_certificate((domain, 443))
                result['details']['ssl'] = {
                    'has_certificate': True,
                    'certificate_info': '存在有效证书' if cert else '无证书'
                }
            except Exception as e:
                result['details']['ssl'] = {
                    'has_certificate': False,
                    'error': str(e)
                }

    except requests.exceptions.Timeout:
        result['errors'].append("连接超时")
    except requests.exceptions.SSLError as e:
        result['errors'].append(f"SSL证书验证失败: {str(e)}")
    except requests.exceptions.ConnectionError as e:
        result['errors'].append(f"连接错误: {str(e)}")
    except Exception as e:
        result['errors'].append(f"未知错误: {str(e)}")

    return result

