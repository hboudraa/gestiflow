from django import forms
from .models import Location

class LocationForm(forms.ModelForm):
    class Meta:
        model  = Location
        fields = ['client','date_debut','date_fin_prevue','depot_garantie','notes']
        widgets = {
            'client':         forms.Select(attrs={'class':'form-select'}),
            'date_debut':     forms.DateTimeInput(attrs={'class':'form-control','type':'datetime-local'}),
            'date_fin_prevue':forms.DateTimeInput(attrs={'class':'form-control','type':'datetime-local'}),
            'depot_garantie': forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'notes':          forms.Textarea(attrs={'class':'form-control','rows':2}),
        }
