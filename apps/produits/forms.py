from django import forms
from .models import Produit, Categorie
from apps.core.sanitizers import sanitize_text, sanitize_reference

class ProduitForm(forms.ModelForm):
    class Meta:
        model  = Produit
        fields = ['reference','nom','description','categorie','fournisseur',
                  'code_barre','image','prix_achat','prix_vente','prix_location',
                  'tva','unite','quantite_stock','seuil_alerte',
                  'actif','peut_vendre','peut_louer']
        widgets = {
            'reference':     forms.TextInput(attrs={'class':'form-control'}),
            'nom':           forms.TextInput(attrs={'class':'form-control'}),
            'description':   forms.Textarea(attrs={'class':'form-control','rows':3}),
            'categorie':     forms.Select(attrs={'class':'form-select'}),
            'fournisseur':   forms.Select(attrs={'class':'form-select'}),
            'code_barre':    forms.TextInput(attrs={'class':'form-control'}),
            'prix_achat':    forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'prix_vente':    forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'prix_location': forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'tva':           forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'unite':         forms.Select(attrs={'class':'form-select'}),
            'quantite_stock':forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'seuil_alerte':  forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'actif':         forms.CheckboxInput(attrs={'class':'form-check-input'}),
            'peut_vendre':   forms.CheckboxInput(attrs={'class':'form-check-input'}),
            'peut_louer':    forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }
    def clean_reference(self):
        return sanitize_reference(self.cleaned_data.get('reference',''))
    def clean_nom(self):
        return sanitize_text(self.cleaned_data.get('nom',''), max_length=200)

class CategorieForm(forms.ModelForm):
    class Meta:
        model  = Categorie
        fields = ['nom','icone','couleur']
        widgets = {
            'nom':    forms.TextInput(attrs={'class':'form-control'}),
            'icone':  forms.TextInput(attrs={'class':'form-control','placeholder':'bi-tag'}),
            'couleur':forms.TextInput(attrs={'class':'form-control','type':'color'}),
        }

class AjustementStockForm(forms.Form):
    type_mouvement = forms.ChoiceField(
        choices=[('entree','Entree'),('sortie_vente','Sortie'),('ajustement','Ajustement'),('perte','Perte/Casse')],
        widget=forms.Select(attrs={'class':'form-select'})
    )
    quantite = forms.DecimalField(min_value=0, widget=forms.NumberInput(attrs={'class':'form-control','step':'0.01'}))
    raison   = forms.CharField(required=False, max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}))
