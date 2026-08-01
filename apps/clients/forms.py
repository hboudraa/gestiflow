from django import forms
from .models import Client
from apps.core.sanitizers import sanitize_text

class ClientForm(forms.ModelForm):
    class Meta:
        model  = Client
        fields = ['nom','type_client','telephone','telephone2','email',
                  'adresse_ligne1','ville','wilaya','code_postal',
                  'registre_commerce','nif','nis',
                  'limite_credit','remise_defaut','notes','actif']
        widgets = {
            'nom':              forms.TextInput(attrs={'class':'form-control'}),
            'type_client':      forms.Select(attrs={'class':'form-select'}),
            'telephone':        forms.TextInput(attrs={'class':'form-control'}),
            'telephone2':       forms.TextInput(attrs={'class':'form-control'}),
            'email':            forms.EmailInput(attrs={'class':'form-control'}),
            'adresse_ligne1':   forms.TextInput(attrs={'class':'form-control'}),
            'ville':            forms.TextInput(attrs={'class':'form-control'}),
            'wilaya':           forms.TextInput(attrs={'class':'form-control'}),
            'code_postal':      forms.TextInput(attrs={'class':'form-control'}),
            'registre_commerce':forms.TextInput(attrs={'class':'form-control'}),
            'nif':              forms.TextInput(attrs={'class':'form-control'}),
            'nis':              forms.TextInput(attrs={'class':'form-control'}),
            'limite_credit':    forms.NumberInput(attrs={'class':'form-control'}),
            'remise_defaut':    forms.NumberInput(attrs={'class':'form-control','step':'0.5'}),
            'notes':            forms.Textarea(attrs={'class':'form-control','rows':3}),
            'actif':            forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }

    def clean_nom(self):
        return sanitize_text(self.cleaned_data.get('nom',''), max_length=200)

    def clean_remise_defaut(self):
        val = self.cleaned_data.get('remise_defaut', 0)
        if val < 0 or val > 100:
            raise forms.ValidationError("La remise doit etre entre 0 et 100%.")
        return val
