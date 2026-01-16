import os
import uuid

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from EasyTesting.settings import FILE_ROOT
import json


@csrf_exempt
def upload_file(request):
    """
    文件上传接口
    支持两种方式：
    1. multipart/form-data (标准文件上传)
    2. JSON格式 (带文件元数据)
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': '只支持POST请求'
        }, status=405)

    try:
        # 方式1: 检查是否有文件上传 (multipart/form-data)
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']

            # 生成唯一文件名，防止重名
            original_name = uploaded_file.name
            file_ext = os.path.splitext(original_name)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"

            # 确保上传目录存在
            upload_dir = getattr(settings, 'FILE_ROOT')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir, exist_ok=True)

            # 保存文件
            file_path = os.path.join(upload_dir, unique_filename)

            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            return JsonResponse({
                'success': True,
                'file_id': unique_filename,
                'file_name': original_name,
                'file_path': file_path,
                'file_url': f'/media/{unique_filename}',  # 如果配置了media URL
                'file_size': uploaded_file.size,
                'content_type': uploaded_file.content_type,
                'message': '文件上传成功'
            },encoder=json.JSONEncoder)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': '文件上传失败: ' + str(e)
        }, status=500)