from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_no = forms.CharField(max_length=10)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_no', 'password1', 'password2']
