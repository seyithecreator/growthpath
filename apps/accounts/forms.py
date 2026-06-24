from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    university = forms.CharField(max_length=200, required=False)
    department = forms.CharField(max_length=200, required=False)
    year_of_study = forms.ChoiceField(
        choices=[('', 'Select level…')] + User.UNIVERSITY_YEAR_CHOICES,
        required=False,
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'university', 'department', 'year_of_study',
            'password1', 'password2',
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.university = self.cleaned_data.get('university', '')
        user.department = self.cleaned_data.get('department', '')
        year = self.cleaned_data.get('year_of_study')
        user.year_of_study = int(year) if year else None
        if commit:
            user.save()
        return user
