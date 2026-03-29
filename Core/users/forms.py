from django import forms
from .models import UserProfile

class OnboardingForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = ['user']
        widgets = {
            'focus_areas': forms.CheckboxSelectMultiple(choices=UserProfile.FOCUS_CHOICES),
        }