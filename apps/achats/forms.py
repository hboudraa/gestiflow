from django import forms
from .models import AchatFournisseur

class AchatForm(forms.ModelForm):
    class Meta:
        model  = AchatFournisseur
        fields = ['fournisseur','date_achat','notes']
        widgets = {
            'fournisseur': forms.Select(attrs={'class':'form-select'}),
            'date_achat':  forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'notes':       forms.Textarea(attrs={'class':'form-control','rows':2}),
        }
