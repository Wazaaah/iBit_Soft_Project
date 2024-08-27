# forms.py
from django import forms


class UserMonthlyForm(forms.Form):
    user_id = forms.IntegerField(required=True, label="User ID")


class TimeframeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Start Date')
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='End Date')


class UserTimeframeForm(forms.Form):
    user_id = forms.IntegerField(required=True, label="User ID")
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label="Start Date")
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label="End Date")
