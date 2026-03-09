from django.urls import path
from django.urls import path
from . import views

urlpatterns = [
    path('mon-code/', views.afficher_code_parrainage, name='mon_code_parrainage'),
    path('mes-filleuls/', views.liste_filleuls, name='liste_filleuls'),
    path('bonus/', views.liste_bonus_parrainage, name='liste_bonus_parrainage'),
]
