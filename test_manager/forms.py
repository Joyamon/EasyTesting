from django import forms
from .models import (
    Project, Environment, TestCase, TestSuite, TestRun, EmailConfig, TestSuiteGroup, TestCaseGroup, TestReport
)
import json


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class EnvironmentForm(forms.ModelForm):
    variables_json = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        help_text='输入json类型的环境变量, 例如., {"key1": "value1", "key2": "value2"}'
    )

    class Meta:
        model = Environment
        fields = ['name', 'project', 'base_url']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['variables_json'].initial = json.dumps(self.instance.variables, ensure_ascii=False, indent=2)

    def clean_variables_json(self):
        variables_json = self.cleaned_data.get('variables_json')
        if not variables_json:
            return {}

        try:
            return json.loads(variables_json)
        except json.JSONDecodeError:
            raise forms.ValidationError('Invalid JSON format')

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.variables = self.cleaned_data.get('variables_json', {})
        if commit:
            instance.save()
        return instance


class TestCaseForm(forms.ModelForm):
    request_headers_json = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        help_text='Enter headers as JSON, e.g., {"Content-Type": "application/json"}'
    )

    request_body_json = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6}),
        required=False,
        help_text='Enter request body as JSON'
    )

    request_body_form_data = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
        required=False,
        help_text='Enter form data as key-value pairs, one per line (e.g., key=value)'
    )

    validation_rules_json = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6}),
        required=False,
        help_text='Enter validation rules as JSON array, e.g., [{"eq": ["$.data.id", 1]}]'
    )

    extract_params_json = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6}),
        required=False,
        help_text='Enter extract parameters as JSON array, e.g., [{"name": "token", "path": "$.data.token"}]'
    )

    class Meta:
        model = TestCase
        fields =  [
            'name', 'project', 'group', 'description', 'request_method',
            'request_url', 'expected_status_code', 'request_body_format'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['request_headers_json'].initial = json.dumps(self.instance.request_headers, indent=2)

            # 根据请求体格式初始化相应的字段
            if self.instance.request_body:
                if self.instance.request_body_format == 'json':
                    self.fields['request_body_json'].initial = json.dumps(self.instance.request_body,
                                                                          ensure_ascii=False, indent=2)
                elif self.instance.request_body_format == 'form-data':
                    # 将字典转换为键值对格式
                    form_data_lines = []
                    for key, value in self.instance.request_body.items():
                        form_data_lines.append(f"{key}={value}")
                    self.fields['request_body_form_data'].initial = "\n".join(form_data_lines)

            self.fields['validation_rules_json'].initial = json.dumps(self.instance.validation_rules,
                                                                      ensure_ascii=False, indent=2)
            self.fields['extract_params_json'].initial = json.dumps(self.instance.extract_params, ensure_ascii=False,
                                                                    indent=2)

    def clean_request_headers_json(self):
        headers_json = self.cleaned_data.get('request_headers_json')
        if not headers_json:
            return {}

        try:
            return json.loads(headers_json)
        except json.JSONDecodeError:
            raise forms.ValidationError('Invalid JSON format')

    def clean_request_body_json(self):
        body_json = self.cleaned_data.get('request_body_json')
        if not body_json:
            return None

        try:
            return json.loads(body_json)
        except json.JSONDecodeError:
            raise forms.ValidationError('Invalid JSON format')

    def clean_request_body_form_data(self):
        form_data = self.cleaned_data.get('request_body_form_data')
        if not form_data:
            return {}

        result = {}
        for line in form_data.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                result[key.strip()] = value.strip()

        return result

    def clean_validation_rules_json(self):
        rules_json = self.cleaned_data.get('validation_rules_json')
        if not rules_json:
            return []

        try:
            return json.loads(rules_json)
        except json.JSONDecodeError:
            raise forms.ValidationError('Invalid JSON format')

    def clean_extract_params_json(self):
        extract_json = self.cleaned_data.get('extract_params_json')
        if not extract_json:
            return []

        try:
            return json.loads(extract_json)
        except json.JSONDecodeError:
            raise forms.ValidationError('Invalid JSON format')

    def clean(self):
        cleaned_data = super().clean()
        request_body_format = cleaned_data.get('request_body_format')

        # 根据选择的请求体格式验证相应的字段
        if request_body_format == 'json':
            if not cleaned_data.get('request_body_json') and cleaned_data.get('request_method') in ['POST', 'PUT',
                                                                                                    'PATCH']:
                self.add_error('request_body_json', 'Request body is required for this method when using JSON format')
        elif request_body_format == 'form-data':
            if not cleaned_data.get('request_body_form_data') and cleaned_data.get('request_method') in ['POST', 'PUT',
                                                                                                         'PATCH']:
                self.add_error('request_body_form_data', 'Form data is required for this method')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.request_headers = self.cleaned_data.get('request_headers_json', {})

        # 根据请求体格式保存相应的数据
        request_body_format = self.cleaned_data.get('request_body_format')
        if request_body_format == 'json':
            instance.request_body = self.cleaned_data.get('request_body_json')
        elif request_body_format == 'form-data':
            instance.request_body = self.cleaned_data.get('request_body_form_data', {})

        instance.validation_rules = self.cleaned_data.get('validation_rules_json', [])
        instance.extract_params = self.cleaned_data.get('extract_params_json', [])
        if commit:
            instance.save()
        return instance


class TestSuiteForm(forms.ModelForm):
    class Meta:
        model = TestSuite
        fields = ['name', 'project', 'group', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class TestRunForm(forms.ModelForm):
    class Meta:
        model = TestRun
        fields = ['name', 'project', 'test_suite', 'environment']


from django import forms


class EmailConfigForm(forms.ModelForm):
    """邮件配置表单"""

    class Meta:
        model = EmailConfig
        fields = [
            'name', 'is_active', 'email_backend',
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
            'smtp_use_tls', 'smtp_use_ssl',
            'api_key',
            'default_from_email', 'default_from_name',
        ]
        widgets = {
            'smtp_password': forms.PasswordInput(render_value=True),
            'api_key': forms.PasswordInput(render_value=True),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加帮助文本
        self.fields['smtp_host'].help_text = "例如: smtp.gmail.com, smtp.qq.com"
        self.fields['smtp_port'].help_text = "常见端口: 25, 465(SSL), 587(TLS)"
        self.fields['api_key'].help_text = "如果使用 SendGrid 或 Mailgun，请输入 API 密钥"
        self.fields['default_from_email'].help_text = "发件人邮箱地址"
        self.fields['default_from_name'].help_text = "发件人显示名称"

        # 设置必填字段
        self.fields['name'].required = True
        self.fields['default_from_email'].required = True
        self.fields['default_from_name'].required = True


class TestEmailForm(forms.Form):
    """测试邮件表单"""
    email = forms.EmailField(label="测试邮箱", help_text="用于接收测试邮件的邮箱地址")


# 新增测试用例分组表单
class TestCaseGroupForm(forms.ModelForm):
    class Meta:
        model = TestCaseGroup
        fields = ['name', 'project', 'parent']
        widgets = {
            'parent': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop('project_id', None)
        super().__init__(*args, **kwargs)

        if project_id:
            self.fields['project'].initial = project_id
            self.fields['project'].widget = forms.HiddenInput()
            # 只显示当前项目的分组
            self.fields['parent'].queryset = TestCaseGroup.objects.filter(project_id=project_id)

        # 如果是编辑模式，排除自己及其子分组，防止循环引用
        if self.instance.pk:
            exclude_ids = [self.instance.pk]
            children = TestCaseGroup.objects.filter(parent=self.instance)
            for child in children:
                exclude_ids.append(child.pk)

                # 递归获取所有子分组
                def get_child_ids(parent_id):
                    child_groups = TestCaseGroup.objects.filter(parent_id=parent_id)
                    for cg in child_groups:
                        exclude_ids.append(cg.pk)
                        get_child_ids(cg.pk)

                get_child_ids(child.pk)

            self.fields['parent'].queryset = self.fields['parent'].queryset.exclude(pk__in=exclude_ids)


# 新增测试套件分组表单
class TestSuiteGroupForm(forms.ModelForm):
    class Meta:
        model = TestSuiteGroup
        fields = ['name', 'project', 'parent']
        widgets = {
            'parent': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop('project_id', None)
        super().__init__(*args, **kwargs)

        if project_id:
            self.fields['project'].initial = project_id
            self.fields['project'].widget = forms.HiddenInput()
            # 只显示当前项目的分组
            self.fields['parent'].queryset = TestSuiteGroup.objects.filter(project_id=project_id)

        # 如果是编辑模式，排除自己及其子分组，防止循环引用
        if self.instance.pk:
            exclude_ids = [self.instance.pk]
            children = TestSuiteGroup.objects.filter(parent=self.instance)
            for child in children:
                exclude_ids.append(child.pk)

                # 递归获取所有子分组
                def get_child_ids(parent_id):
                    child_groups = TestSuiteGroup.objects.filter(parent_id=parent_id)
                    for cg in child_groups:
                        exclude_ids.append(cg.pk)
                        get_child_ids(cg.pk)

                get_child_ids(child.pk)

            self.fields['parent'].queryset = self.fields['parent'].queryset.exclude(pk__in=exclude_ids)


class TestReportForm(forms.ModelForm):
    class Meta:
        model = TestReport
        fields = ['name', 'description', 'report_format', 'is_public']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class GenerateReportForm(forms.Form):
    name = forms.CharField(max_length=255)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    report_format = forms.ChoiceField(choices=TestReport.REPORT_FORMAT_CHOICES)
    is_public = forms.BooleanField(required=False, initial=False)
