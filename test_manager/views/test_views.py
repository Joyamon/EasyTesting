from django.shortcuts import render


def ui_test_page(request):
    return render(request, "test/ui.html")
