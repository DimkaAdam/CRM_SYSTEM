from django import forms
from .models import Contact, Company, ContactMaterial

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['address', 'company_type']


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'unique_number']


# Edit price form
class ContactMaterialForm(forms.ModelForm):
    class Meta:
        model = ContactMaterial
        fields = ['material','price']

