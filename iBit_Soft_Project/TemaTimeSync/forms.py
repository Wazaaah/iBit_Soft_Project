# forms.py
from django import forms


class UserMonthlyForm(forms.Form):
    user_name = forms.CharField(required=True,label="Name")


class TimeframeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Start Date')
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='End Date')


class UserTimeframeForm(forms.Form):
    user_name = forms.CharField(required=True,label="Name")
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label="Start Date")
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label="End Date")


   
