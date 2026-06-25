"""apps/goals/forms.py"""

from django import forms
from django.utils import timezone
from .models import Goal, Milestone


class GoalForm(forms.ModelForm):
    target_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'gp-form-control'}),
        label='Target date'
    )

    class Meta:
        model = Goal
        fields = [
            'title', 'description', 'category', 'priority',
            'success_metric', 'target_value', 'target_date', 'notes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'gp-form-control', 'placeholder': 'e.g. Complete Python certification'}),
            'description': forms.Textarea(attrs={'class': 'gp-form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'gp-form-control'}),
            'priority': forms.Select(attrs={'class': 'gp-form-control'}),
            'success_metric': forms.TextInput(attrs={'class': 'gp-form-control', 'placeholder': 'e.g. Score 80%+ on final exam'}),
            'target_value': forms.NumberInput(attrs={'class': 'gp-form-control'}),
            'notes': forms.Textarea(attrs={'class': 'gp-form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_target_date(self):
        d = self.cleaned_data['target_date']
        if d < timezone.now().date():
            raise forms.ValidationError('Target date cannot be in the past.')
        return d


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['title', 'description', 'target_date', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'gp-form-control'}),
            'description': forms.Textarea(attrs={'class': 'gp-form-control', 'rows': 2}),
            'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'gp-form-control'}),
            'order': forms.NumberInput(attrs={'class': 'gp-form-control'}),
        }
