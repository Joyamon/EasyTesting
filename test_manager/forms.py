from django import forms
from .models import (
    Project, Environment, TestCase, TestSuite, TestRun, EmailConfig
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
        help_text='Enter variables as JSON, e.g., {"key1": "value1", "key2": "value2"}'
    )

    class Meta:
        model = Environment
        fields = ['name', 'project', 'base_url']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['variables_json'].initial = json.dumps(self.instance.variables, indent=2)

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

    class Meta:
        model = TestCase
        fields = [
            'name', 'project', 'description', 'request_method',
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
                    self.fields['request_body_json'].initial = json.dumps(self.instance.request_body, indent=2)
                elif self.instance.request_body_format == 'form-data':
                    # 将字典转换为键值对格式
                    form_data_lines = []
                    for key, value in self.instance.request_body.items():
                        form_data_lines.append(f"{key}={value}")
                    self.fields['request_body_form_data'].initial = "\n".join(form_data_lines)

            self.fields['validation_rules_json'].initial = json.dumps(self.instance.validation_rules, indent=2)

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
        if commit:
            instance.save()
        return instance


class TestSuiteForm(forms.ModelForm):
    class Meta:
        model = TestSuite
        fields = ['name', 'project', 'description']
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
