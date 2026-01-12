import json
import ast
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from test_manager.forms import MockDataForm
from test_manager.model.mockdata import MockData
from test_manager.utils.gen_data import auto_gen_data
from test_manager.views.common import paginate_queryset


@login_required
def mock_data_generator(request):
    data_list = request.POST.get('data')
    num = request.POST.get('num')
    if request.method == 'POST':
        form = MockDataForm(request.POST)
        if form.is_valid():
            mock_data = form.save(commit=False)
            mock_data.data = auto_gen_data(fields=ast.literal_eval(data_list), num=int(num))
            mock_data.created_by = request.user
            mock_data.save()
            messages.success(request, '数据生成成功')
            return redirect('mock-data-list')
    else:

        form = MockDataForm()
    return render(request, 'test_manager/mock_data_form.html', {'form': form, 'title': '生成数据'})


def mock_data_list(request):
    all_mock_data = MockData.objects.all().order_by('-created_at')
    # 获取每页显示的记录数
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10
    mock_data_list = paginate_queryset(request, all_mock_data, per_page)
    context = {
        'mock_data_list': mock_data_list,
        'per_page': per_page,
    }
    return render(request, 'test_manager/mock_data.html', context)


def mock_data_delete(request, pk):
    mock_data = get_object_or_404(MockData, pk=pk)
    if request.method == 'POST':
        mock_data.delete()
        messages.success(request, '数据删除成功')
        return redirect('mock-data-list')
    return render(request, 'test_manager/mock_data_delete.html', {'mock_data': mock_data})


def mock_data_export(request, pk):
    data = MockData.objects.get(pk=pk)
    data = json.loads(data.data)
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    # 创建响应对象
    response = HttpResponse(json_str, content_type='application/json')
    # 设置Content-Disposition为附件下载，并指定文件名
    response['Content-Disposition'] = 'attachment; filename="mock_data.json"'
    return response
