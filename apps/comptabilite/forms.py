from django import forms
from .models import Transaction, CategorieDepense

class TransactionForm(forms.ModelForm):
    class Meta:
        model  = Transaction
        fields = ['type_transaction','montant','libelle','date_transaction','mode_reglement','categorie','reference']
        widgets = {
            'type_transaction':forms.Select(attrs={'class':'form-select'}),
            'montant':         forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'libelle':         forms.TextInput(attrs={'class':'form-control'}),
            'date_transaction':forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'mode_reglement':  forms.Select(attrs={'class':'form-select'}),
            'categorie':       forms.Select(attrs={'class':'form-select'}),
            'reference':       forms.TextInput(attrs={'class':'form-control'}),
        }
