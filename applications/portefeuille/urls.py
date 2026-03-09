from django.urls import path
from . import views

urlpatterns = [
    path('transactions/', views.liste_transactions, name='liste_transactions'),
    path('solde/', views.afficher_solde, name='afficher_solde'),
]
