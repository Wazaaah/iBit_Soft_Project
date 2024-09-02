# forms.py
from django import forms
from django.utils import timezone
from django.contrib.auth.models import User

class UserMonthlyForm(forms.Form):
    user_id = forms.ModelChoiceField(queryset=User.objects.all(), label="Select User")
    month = forms.IntegerField(min_value=1, max_value=12, label="Month", required=False)
    year = forms.IntegerField(min_value=2000, max_value=timezone.now().year, label="Year", required=False)


class TimeframeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Start Date')
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='End Date')


# forms.py
class UserTimeframeForm(forms.Form):
    user_id = forms.ModelChoiceField(queryset=User.objects.all(), label="Select User")
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Start Date")
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="End Date")

class PayrollMonthForm(forms.Form):
    month = forms.ChoiceField(choices=[(i, f'{i}') for i in range(1, 13)], label='Month')
    year = forms.ChoiceField(choices=[(i, f'{i}') for i in range(2020, timezone.now().year + 1)], label='Year')


class MultiDateSelectionForm(forms.Form):
    dates = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter dates separated by commas or new lines'}),
        label="Select Dates"
    )

class UniqueYearIDForm(forms.ModelForm):
    year_id = forms.CharField(max_length=4)

    class Meta:
        model = User  # Assuming this is stored in the User model
        fields = ['year_id']

    def clean_year_id(self):
        year_id = self.cleaned_data.get('year_id')
        if len(year_id) != 4:
            raise forms.ValidationError('Year ID must be exactly 4 characters.')
        if User.objects.filter(year_id=year_id).exists():
            raise forms.ValidationError('Year ID must be unique.')
        return year_id
