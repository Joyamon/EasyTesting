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

    validation_rules_json = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6}),
        required=False,
        help_text='Enter validation rules as JSON array, e.g., [{"eq": ["$.data.id", 1]}]'
    )

    class Meta:
        model = TestCase
        fields = [
            'name', 'project', 'description', 'request_method',
            'request_url', 'expected_status_code'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['request_headers_json'].initial = json.dumps(self.instance.request_headers, indent=2)
            self.fields['request_body_json'].initial = json.dumps(self.instance.request_body,
                                                                  indent=2) if self.instance.request_body else ''
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

    def clean_validation_rules_json(self):
        rules_json = self.cleaned_data.get('validation_rules_json')
        if not rules_json:
            return []

        try:
            return json.loads(rules_json)
        except json.JSONDecodeError:
            raise forms.ValidationError('Invalid JSON format')

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.request_headers = self.cleaned_data.get('request_headers_json', {})
        instance.request_body = self.cleaned_data.get('request_body_json')
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
