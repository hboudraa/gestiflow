from django import forms
from .models import OrdreDeTravail

class OrdreDeTravailForm(forms.ModelForm):
    class Meta:
        model  = OrdreDeTravail
        fields = ['client','technicien','objet_service','description_probleme',
                  'priorite','date_entree','date_fin_prevue','cout_main_oeuvre','tva','note_client']
        widgets = {
            'client':              forms.Select(attrs={'class':'form-select'}),
            'technicien':          forms.Select(attrs={'class':'form-select'}),
            'objet_service':       forms.TextInput(attrs={'class':'form-control'}),
            'description_probleme':forms.Textarea(attrs={'class':'form-control','rows':3}),
            'priorite':            forms.Select(attrs={'class':'form-select'}),
            'date_entree':         forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'date_fin_prevue':     forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'cout_main_oeuvre':    forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'tva':                 forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'note_client':         forms.Textarea(attrs={'class':'form-control','rows':2}),
        }
