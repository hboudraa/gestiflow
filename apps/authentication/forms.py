from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Utilisateur

class ConnexionForm(forms.Form):
    username = forms.CharField(
        label="Identifiant",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Identifiant', 'autofocus': True})
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'})
    )

class UtilisateurForm(forms.ModelForm):
    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput(attrs={'class':'form-control'}), required=False)
    password2 = forms.CharField(label='Confirmer', widget=forms.PasswordInput(attrs={'class':'form-control'}), required=False)

    class Meta:
        model  = Utilisateur
        fields = ['username','first_name','last_name','email','telephone','role','actif']
        widgets = {f: forms.TextInput(attrs={'class':'form-control'}) for f in ['username','first_name','last_name','email','telephone']}
        widgets['role']  = forms.Select(attrs={'class':'form-select'})
        widgets['actif'] = forms.CheckboxInput(attrs={'class':'form-check-input'})

    def clean(self):
        cd = super().clean()
        p1, p2 = cd.get('password1'), cd.get('password2')
        if p1 and p1 != p2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cd

    def save(self, commit=True):
        user = super().save(commit=False)
        p1 = self.cleaned_data.get('password1')
        if p1: user.set_password(p1)
        if commit: user.save()
        return user
