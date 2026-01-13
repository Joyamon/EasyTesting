import json
from datetime import datetime
from django.http import HttpResponse
import xlwt


def export_test_case(test_case):
    """导出为Excel格式"""
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="case_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls"'

    # 创建工作簿
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('测试用例')

    # 设置样式
    header_style = xlwt.XFStyle()
    header_font = xlwt.Font()
    header_font.bold = True
    header_style.font = header_font

    # 写入表头
    headers = [
        'ID', '用例名称', '所属项目', '用例分组', '用例描述', '请求方法',
        '请求URL', '请求头', '请求体', '请求体格式',
        '期望状态码', '验证规则', '提取参数', '创建时间', '更新时间', '创建人'
    ]

    for col_idx, header in enumerate(headers):
        ws.write(0, col_idx, header, header_style)
        # 设置列宽
        ws.col(col_idx).width = 256 * 20  # 20个字符宽度

    # 辅助函数：将可能为字典或列表的值转换为JSON字符串
    def convert_value(value):
        if value is None:
            return ''
        if isinstance(value, (dict, list)):
            try:
                return json.dumps(value, ensure_ascii=False, indent=2)
            except:
                return str(value)
        return str(value)

    # 写入数据
    for row_idx, case in enumerate(test_case, 1):
        # 获取项目、分组和创建人的名称
        project_name = case.project.name if hasattr(case, 'project') and case.project else str(case.project_id or '')
        group_name = case.group.name if hasattr(case, 'group') and case.group else str(case.group_id or '')
        creator_name = case.created_by.username if case.created_by else ''

        # 写入数据行
        ws.write(row_idx, 0, case.id or '')
        ws.write(row_idx, 1, case.name or '')
        ws.write(row_idx, 2, project_name)
        ws.write(row_idx, 3, group_name)
        ws.write(row_idx, 4, case.description or '')
        ws.write(row_idx, 5, case.request_method or '')
        ws.write(row_idx, 6, case.request_url or '')
        ws.write(row_idx, 7, convert_value(case.request_headers))
        ws.write(row_idx, 8, convert_value(case.request_body))
        ws.write(row_idx, 9, case.request_body_format or '')
        ws.write(row_idx, 10, convert_value(case.expected_status_code))
        ws.write(row_idx, 11, convert_value(case.validation_rules))
        ws.write(row_idx, 12, convert_value(case.extract_params))
        ws.write(row_idx, 13, case.created_at.strftime('%Y-%m-%d %H:%M:%S') if case.created_at else '')
        ws.write(row_idx, 14, case.updated_at.strftime('%Y-%m-%d %H:%M:%S') if case.updated_at else '')
        ws.write(row_idx, 15, creator_name)

    wb.save(response)
    return response