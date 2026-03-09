from django.urls import path
from . import views

urlpatterns = [
    path('', views.vue_liste_produits, name='liste_produits'),
    path('achat/<int:produit_id>/', views.vue_achat, name='achat'),
    path('mes-investissements/', views.mes_investissements, name='mes_investissements'), 
]
