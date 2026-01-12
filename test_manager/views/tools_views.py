from django.shortcuts import render


def tools(request):
    return render(request, 'test_manager/tools.html')
