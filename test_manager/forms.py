from django import forms
from .models import (
    Project, Environment, TestCase, TestSuite, TestRun
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
