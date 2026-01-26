import json
import re
from django.http import JsonResponse
from django.shortcuts import render

from test_manager.utils.db import connect_mysql


def tools(request):
    return render(request, 'test_manager/tools.html')


def con_mysql(request):
    if request.content_type == 'application/json':
        data = json.loads(request.body)
    else:
        # 表单数据
        data = request.POST.dict()

    if request.method == 'GET':
        return render(request, 'db/con_db.html')
    if request.method != 'POST':
        return JsonResponse(data={'error': 'Method not allowed'}, status=405, safe=False)

    # 验证必要参数
    sql = data.pop('sql')
    print("sql", sql)
    if not sql:
        return JsonResponse(data={'error': 'SQL parameter is required'}, status=400, safe=False)

    # 基本SQL安全检查 - 禁止危险操作
    sql_lower = sql.strip().lower()
    dangerous_keywords = ['drop', 'delete', 'truncate', 'alter', 'create', 'update', 'insert']
    if any(keyword in sql_lower for keyword in dangerous_keywords):
        return JsonResponse(data={'error': 'Dangerous SQL operation not allowed'}, status=400, safe=False)

    # 验证SQL格式 - 只允许SELECT查询
    if not re.match(r'^\s*select\s+', sql_lower):
        return JsonResponse(data={'error': 'Only SELECT statements are allowed'}, status=400, safe=False)

    kwargs_param = json.loads(json.dumps(data))
    keys_to_remove = ["db_type", "connection_name"]
    connection_info = {k: v for k, v in kwargs_param.items() if k not in keys_to_remove}
    port = int(connection_info.pop('port'))
    connection_info['port'] = port
    print("", connection_info)
    if not connection_info:
        return JsonResponse(data={'error': 'Kwargs parameter is required'}, status=400, safe=False)

    try:

        if not isinstance(connection_info, dict):
            return JsonResponse(data={'error': 'Kwargs must be a valid JSON object'}, status=400, safe=False)
    except json.JSONDecodeError:
        return JsonResponse(data={'error': 'Invalid JSON format for kwargs'}, status=400, safe=False)

    # 执行数据库查询
    df = connect_mysql(sql, **connection_info).to_dict(orient='records')
    return JsonResponse({'data': df, 'success': True})
