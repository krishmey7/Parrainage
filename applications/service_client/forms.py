from django import forms
from .models import Requete, Reponse

class RequeteForm(forms.ModelForm):
    """Formulaire pour créer une requête"""
    
    class Meta:
        model = Requete
        fields = ['nom_complet', 'telephone', 'titre', 'description', 'priorite', 'categorie']
        widgets = {
            'nom_complet': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre nom complet',
                'required': True
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre numéro de téléphone',
                'required': True
            }),
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de votre requête',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Décrivez votre problème ou votre demande en détail...',
                'required': True
            }),
            'priorite': forms.Select(attrs={
                'class': 'form-control'
            }),
            'categorie': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Bug, Demande de fonctionnalité, Question...'
            })
        }
        labels = {
            'nom_complet': 'Nom complet',
            'telephone': 'Téléphone',
            'titre': 'Titre de la requête',
            'description': 'Description détaillée',
            'priorite': 'Priorité',
            'categorie': 'Catégorie'
        }

class ReponseForm(forms.ModelForm):
    """Formulaire pour ajouter une réponse"""
    
    class Meta:
        model = Reponse
        fields = ['message', 'est_interne']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Votre message...',
                'required': True
            }),
            'est_interne': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'message': 'Message',
            'est_interne': 'Note interne (non visible par le client)'
        }
