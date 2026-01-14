from django.http import JsonResponse
from test_manager.utils.check_url import check_website_enhanced


def check_website(request):
    url = request.GET.get('url')
    res = check_website_enhanced(url)
    context = {
        "URL": res["url"],
        "checkTime": res["timestamp"],
        "is_valid": "✅正常" if res.get("is_valid") == True else "❌无效",
        "status_code": res["status_code"] if res["is_valid"] else "",
        "during": res['response_time_ms'] if res['is_valid'] else "",
        "DNS": res["details"]["dns_resolution"]["ip_address"] if "dns_resolution" in res["details"] else "",
        "details": res['details']
    }
    # 安全获取DNS信息
    if "details" in res and "dns_resolution" in res["details"]:
        context["DNS"] = res["details"]["dns_resolution"].get("ip_address", "")
    return JsonResponse(context, json_dumps_params={'ensure_ascii': False})
