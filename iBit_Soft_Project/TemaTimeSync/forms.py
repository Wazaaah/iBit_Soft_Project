# forms.py
from django import forms
from django.utils import timezone


class UserMonthlyForm(forms.Form):
    user_id = forms.IntegerField(required=True, label="User ID")


class TimeframeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Start Date')
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='End Date')


class UserTimeframeForm(forms.Form):
    user_id = forms.IntegerField(required=True, label="User ID")
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label="Start Date")
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label="End Date")


class PayrollMonthForm(forms.Form):
    month = forms.ChoiceField(choices=[(i, f'{i}') for i in range(1, 13)], label='Month')
    year = forms.ChoiceField(choices=[(i, f'{i}') for i in range(2020, timezone.now().year + 1)], label='Year')


class MultiDateSelectionForm(forms.Form):
    dates = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter dates separated by commas or new lines'}),
        label="Select Dates"
    )
