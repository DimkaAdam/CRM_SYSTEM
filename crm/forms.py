from django import forms
from .models import Contact, Company, ContactMaterial, Deals

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['address', 'company_type']


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'unique_number','pickup_requested']


# Edit price form
class ContactMaterialForm(forms.ModelForm):
    class Meta:
        model = ContactMaterial
        fields = ['material','price']


class DealForm(forms.ModelForm):
    class Meta:
        model = Deals
        fields = [
            'date', 'supplier', 'buyer', 'grade', 'shipped_quantity', 'shipped_pallets',
            'scale_ticket', 'received_quantity', 'received_pallets', 'supplier_price',
            'supplier_currency', 'supplier_total', 'buyer_price', 'buyer_currency',
            'total_amount', 'invoice_number', 'paid_date', 'transport_cost', 'transport_company',
            'total_income_loss'
        ]

        # Указываем виджеты для улучшения отображения, например, для дат или валют
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'paid_date': forms.DateInput(attrs={'type': 'date'}),
            'supplier_price': forms.NumberInput(attrs={'step': '0.01'}),
            'buyer_price': forms.NumberInput(attrs={'step': '0.01'}),
            'transport_cost': forms.NumberInput(attrs={'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'total_income_loss': forms.NumberInput(attrs={'step': '0.01'}),
        }