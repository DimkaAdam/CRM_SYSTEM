from django import forms
from .models import Contact, Company

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['address', 'company_type', 'current_price']


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'unique_number']