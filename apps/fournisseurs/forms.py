from django import forms
from .models import Fournisseur

class FournisseurForm(forms.ModelForm):
    class Meta:
        model  = Fournisseur
        fields = ['nom','telephone','telephone2','email','contact_nom',
                  'adresse_ligne1','ville','wilaya',
                  'registre_commerce','nif','delai_paiement','remise_habituelle','notes','actif']
        widgets = {f: forms.TextInput(attrs={'class':'form-control'}) for f in
                   ['nom','telephone','telephone2','email','contact_nom','adresse_ligne1','ville','wilaya','registre_commerce','nif']}
        widgets['delai_paiement']   = forms.NumberInput(attrs={'class':'form-control'})
        widgets['remise_habituelle']= forms.NumberInput(attrs={'class':'form-control','step':'0.5'})
        widgets['notes']            = forms.Textarea(attrs={'class':'form-control','rows':3})
        widgets['actif']            = forms.CheckboxInput(attrs={'class':'form-check-input'})
