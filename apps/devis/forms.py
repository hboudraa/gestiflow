from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import Devis

class DevisForm(forms.ModelForm):
    class Meta:
        model  = Devis
        fields = ['client','commercial','date_devis','date_validite','remise_globale','notes','conditions']
        widgets = {
            'client':        forms.Select(attrs={'class':'form-select'}),
            'commercial':    forms.Select(attrs={'class':'form-select'}),
            'date_devis':    forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'date_validite': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'remise_globale':forms.NumberInput(attrs={'class':'form-control','step':'0.5'}),
            'notes':         forms.Textarea(attrs={'class':'form-control','rows':2}),
            'conditions':    forms.Textarea(attrs={'class':'form-control','rows':2}),
        }
