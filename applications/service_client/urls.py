from django.contrib import admin
from django.urls import include, path
from applications.service_client.views import (
    index, contact, login_view, logout_view, ListeRequetesView, DetailRequeteView, CreerRequeteView,
    ajouter_reponse, recherche_requetes, AdminListeRequetesView,
    AdminDetailRequeteView, admin_ajouter_reponse, admin_changer_statut
)

urlpatterns = [
    # Pages publiques
    path('', index, name='index'),
    path('contact/', contact, name='contact'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # Pages utilisateur (nécessitent une connexion)
    path('requetes/', ListeRequetesView.as_view(), name='liste_requetes'),
    path('requetes/nouvelle/', CreerRequeteView.as_view(), name='creer_requete'),
    path('requetes/<int:pk>/', DetailRequeteView.as_view(), name='detail_requete'),
    path('requetes/<int:pk>/reponse/', ajouter_reponse, name='ajouter_reponse'),
    path('requetes/recherche/', recherche_requetes, name='recherche_requetes'),



    # Pages administration (nécessitent les droits staff)
    path('admin/requetes/', AdminListeRequetesView.as_view(), name='admin_liste_requetes'),
    path('admin/requetes/<int:pk>/', AdminDetailRequeteView.as_view(), name='admin_detail_requete'),
    path('admin/requetes/<int:pk>/reponse/', admin_ajouter_reponse, name='admin_ajouter_reponse'),
    path('admin/requetes/<int:pk>/statut/', admin_changer_statut, name='admin_changer_statut'),
]