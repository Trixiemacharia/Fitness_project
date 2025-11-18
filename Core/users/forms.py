from django import forms
from .models import UserProfile

class OnboardingForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = ['user']
        widgets = {
            'focus_areas': forms.CheckboxSelectMultiple(choices=UserProfile.FOCUS_CHOICES),
            'equipments_available_to_them':forms.CheckboxSelectMultiple(choices=UserProfile.EQUIPMENTS_AVAILABLE_TO_THEM),
        }