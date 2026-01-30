from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.shortcuts import render, redirect

from test_manager.views.auth_views import CustomUserCreationForm
from test_manager.views.common import paginate_queryset


def tester_list(request):
    """测试人员列表"""
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10
    all_testers = User.objects.all()
    testers = paginate_queryset(request, all_testers, per_page)
    context ={
        'testers': testers,
        'per_page': per_page,
        'total_count': all_testers.count()
    }
    return render(request, 'test_manager/tester/tester_list.html', context=context)


def delete_tester(request, pk):
    """删除测试人员"""
    try:
        tester = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            tester.delete()
            messages.success(request, '测试人员删除成功')
            return redirect('test_users_list')
        return render(request, 'test_manager/tester/tester_confirm_delete.html', {'tester': tester})
    except User.DoesNotExist:
        messages.error(request, '测试人员不存在')
    return render(request, 'test_manager/tester/tester_list.html')



