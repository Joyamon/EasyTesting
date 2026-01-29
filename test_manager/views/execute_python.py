import time

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import traceback


@csrf_exempt
def execute_python_code(request):
    """执行Python代码并返回结果"""
    if request.method != 'POST':
        return JsonResponse({'error': '只支持POST请求'}, status=405)

    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        context = data.get('context', {})

        if not code:
            return JsonResponse({'error': '没有提供代码'}, status=400)

        # 创建安全的执行环境
        import datetime, random, json as json_module, math, re, string, uuid, time, hashlib, base64
        from decimal import Decimal

        allowed_modules = {
            'datetime': datetime,
            'random': random,
            'json': json_module,
            'math': math,
            're': re,
            'string': string,
            'uuid': uuid,
            'time': time,
            'hashlib': hashlib,
            'base64': base64,
        }

        # 限制执行环境
        restricted_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'isinstance': isinstance,
                'type': type,
                'None': None,
                'True': True,
                'False': False,
            },
            **allowed_modules
        }

        # 添加上下文
        if context:
            restricted_globals['context'] = context

        # 执行代码
        exec_globals = {}
        wrapped_code = f"""
def generate_request_body(context=None):
{chr(10).join('    ' + line for line in code.strip().split(chr(10)))}

result = generate_request_body(context)
"""

        exec(wrapped_code, restricted_globals, exec_globals)

        # 获取结果
        result = exec_globals.get('result')

        return JsonResponse({
            'success': True,
            'result': result,
            'code': code
        })

    except SyntaxError as e:
        return JsonResponse({
            'success': False,
            'error': f'语法错误: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'执行错误: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=400)


def get_time(context=None):
    return time.time()


print(get_time())
