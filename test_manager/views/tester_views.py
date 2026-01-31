from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.shortcuts import render, redirect
import json
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
    context = {
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


def tester_change_status(request, pk):
    """测试人员状态切换"""
    try:

        tester = User.objects.get(pk=pk)
        data = json.loads(request.body)

        # 使用更清晰的字段名
        is_active = data.get('is_active', False)

        # 防止禁用自己
        if tester == request.user and not is_active:
            return JsonResponse({
                'success': False,
                'message': '不能禁用自己的账号'
            })

        # 管理员才能禁用普通用户
        if not request.user.is_superuser and not is_active:
            return JsonResponse({
                'success': False,
                'message': '权限不足'
            })
        if tester.is_superuser and not is_active:
            return JsonResponse({
                'success': False,
                'message': '不能禁用管理员账号'
            })
        # 更新状态
        tester.is_active = is_active
        tester.is_staff = is_active
        tester.save()

        return JsonResponse({
            'success': True,
            'message': f'账号已{"启用" if is_active else "禁用"}',
            'is_active': is_active
        })

    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '测试人员不存在'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '无效的请求数据'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }, status=500)
