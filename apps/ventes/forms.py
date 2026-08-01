from django import forms
from django.utils import timezone
from .models import Facture, LigneFacture, Paiement

class FactureForm(forms.ModelForm):
    class Meta:
        model  = Facture
        fields = ['client','vendeur','date_facture','date_echeance','remise_globale','notes','conditions']
        widgets = {
            'client':        forms.Select(attrs={'class':'form-select'}),
            'vendeur':       forms.Select(attrs={'class':'form-select'}),
            'date_facture':  forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'date_echeance': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'remise_globale':forms.NumberInput(attrs={'class':'form-control','step':'0.5','min':'0','max':'100'}),
            'notes':         forms.Textarea(attrs={'class':'form-control','rows':2}),
            'conditions':    forms.Textarea(attrs={'class':'form-control','rows':2}),
        }

class PaiementForm(forms.ModelForm):
    class Meta:
        model  = Paiement
        fields = ['montant','date_paiement','mode','reference','notes']
        widgets = {
            'montant':       forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'date_paiement': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'mode':          forms.Select(attrs={'class':'form-select'}),
            'reference':     forms.TextInput(attrs={'class':'form-control'}),
            'notes':         forms.Textarea(attrs={'class':'form-control','rows':2}),
        }
