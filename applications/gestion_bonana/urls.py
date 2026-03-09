# personnel/urls.py
from django.urls import path
from . import views

app_name = 'personnel'

urlpatterns = [
    path('tableau-de-bord/', views.tableau_de_bord_personnel, name='tableau_de_bord'),
    path('objectifs/', views.liste_objectifs, name='liste_objectifs'),
    path('objectifs/<int:objectif_id>/', views.detail_objectif, name='detail_objectif'),
    path('mes-postulations/', views.mes_postulations, name='mes_postulations'),
    path('historique-primes/', views.historique_primes, name='historique_primes'),
]
